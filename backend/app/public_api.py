from __future__ import annotations

import json
import logging
import tempfile
import time
import uuid
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated
from urllib.request import Request as UrlRequest
from urllib.request import urlopen

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

from .config import (
    ALLOWED_DOCX_CONTENT_TYPES,
    ALLOWED_DOCX_EXTENSIONS,
    MAX_TEXT_PRECHECK_CHARS,
    MAX_UPLOAD_SIZE_BYTES,
    PUBLIC_EXPORT_RATE_LIMIT_PER_HOUR,
    PUBLIC_EXPORT_RETENTION_SECONDS,
    turnstile_required,
    turnstile_secret_key,
)
from .contracts import CapabilityFlags, NormalizedThesis, PrecheckResponse
from .errors import AppError
from .security import export_token_for_digest, secret_key, thesis_digest, verify_export_token
from .services.export import export_docx
from .services.parse import normalize_text_input, parse_docx_file
from .services.precheck import run_precheck
from .storage import storage

logger = logging.getLogger("scnu-thesis-portal.public")
router = APIRouter(prefix="/api/public", tags=["public-export"])

_rate_windows: dict[tuple[str, int], int] = defaultdict(int)


class PublicTextPrecheckRequest(BaseModel):
    text: str
    privacy_accepted: bool = False
    turnstile_token: str = ""


class PublicExportDocxRequest(BaseModel):
    thesis: NormalizedThesis
    export_token: str


class PublicExportResponse(BaseModel):
    export_id: str
    download_url: str
    report_url: str
    expires_at: datetime


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",", 1)[0].strip()
    return request.client.host if request.client else "unknown"


def ip_hash(request: Request) -> str:
    return thesis_digest(f"ip:{client_ip(request)}:{secret_key()}")[:24]


def require_privacy(accepted: bool) -> None:
    if not accepted:
        raise AppError("PRIVACY_CONFIRMATION_REQUIRED", "请先确认隐私说明后再继续。", status_code=400)


def enforce_rate_limit(request: Request) -> str:
    hashed = ip_hash(request)
    window = int(time.time() // 3600)
    key = (hashed, window)
    _rate_windows[key] += 1
    for old_key in list(_rate_windows):
        if old_key[1] < window - 1:
            _rate_windows.pop(old_key, None)
    if _rate_windows[key] > PUBLIC_EXPORT_RATE_LIMIT_PER_HOUR:
        raise AppError("RATE_LIMITED", "当前 IP 的公开导出请求过于频繁，请稍后再试。", status_code=429)
    return hashed


def verify_turnstile_or_raise(token: str, request: Request) -> None:
    if not turnstile_required():
        return
    secret = turnstile_secret_key()
    if not secret or not token:
        raise AppError("TURNSTILE_REQUIRED", "请完成人机验证后再提交。", status_code=400)
    payload = json.dumps({"secret": secret, "response": token, "remoteip": client_ip(request)}).encode("utf-8")
    siteverify = UrlRequest(
        "https://challenges.cloudflare.com/turnstile/v0/siteverify",
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urlopen(siteverify, timeout=4) as response:
            result = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise AppError("TURNSTILE_UNAVAILABLE", "人机验证服务暂时不可用，请稍后再试。", status_code=503) from exc
    if not result.get("success"):
        raise AppError("TURNSTILE_INVALID", "人机验证未通过，请刷新后重试。", status_code=400, details={"error_codes": result.get("error-codes", [])})


def attach_public_export_token(response: PrecheckResponse) -> PrecheckResponse:
    expires_at = datetime.now(UTC).replace(tzinfo=None) + timedelta(seconds=PUBLIC_EXPORT_RETENTION_SECONDS)
    digest = thesis_digest(response.thesis.model_dump_json())
    response.export_token = export_token_for_digest(digest, int(expires_at.replace(tzinfo=UTC).timestamp()))
    response.expires_at = expires_at
    return response


def log_public_request(*, request: Request, size: int, status_code: int, error_code: str = "", elapsed_ms: int = 0) -> None:
    logger.info(
        "public_export_event ip_hash=%s file_size=%s status_code=%s error_code=%s elapsed_ms=%s",
        ip_hash(request),
        size,
        status_code,
        error_code,
        elapsed_ms,
    )


@router.post("/precheck/docx", response_model=PrecheckResponse)
async def public_precheck_docx(
    request: Request,
    file: Annotated[UploadFile, File(...)],
    privacy_accepted: Annotated[bool, Form()] = False,
    turnstile_token: Annotated[str, Form()] = "",
) -> PrecheckResponse:
    started = time.perf_counter()
    require_privacy(privacy_accepted)
    verify_turnstile_or_raise(turnstile_token, request)
    enforce_rate_limit(request)
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_DOCX_EXTENSIONS:
        raise AppError("UNSUPPORTED_FILE_TYPE", "请上传 .docx 文件，暂不支持 .doc 或其他格式。", status_code=400)
    if (file.content_type or "") not in ALLOWED_DOCX_CONTENT_TYPES:
        raise AppError("UNSUPPORTED_FILE_TYPE", "文件类型不符合 .docx，请重新选择 Word 文档。", status_code=400)
    payload = await file.read()
    if not payload:
        raise AppError("CONTENT_EMPTY", "上传文件为空，请选择包含论文内容的 .docx 文件。", status_code=400)
    if len(payload) > MAX_UPLOAD_SIZE_BYTES:
        raise AppError("FILE_TOO_LARGE", "文件超过当前上传大小限制，请压缩或删减后再试。", status_code=400)
    if not payload.startswith(b"PK"):
        raise AppError("DOCX_INVALID", "上传文件不是有效的 .docx 文档，请确认文件未损坏。", status_code=400)
    with tempfile.TemporaryDirectory(prefix="scnu-public-docx-") as tmp:
        upload_path = Path(tmp) / "input.docx"
        upload_path.write_bytes(payload)
        response = attach_public_export_token(run_precheck(parse_docx_file(upload_path, CapabilityFlags())))
        log_public_request(request=request, size=len(payload), status_code=200, elapsed_ms=int((time.perf_counter() - started) * 1000))
        return response


@router.post("/precheck/text", response_model=PrecheckResponse)
def public_precheck_text(request: PublicTextPrecheckRequest, raw_request: Request) -> PrecheckResponse:
    require_privacy(request.privacy_accepted)
    verify_turnstile_or_raise(request.turnstile_token, raw_request)
    enforce_rate_limit(raw_request)
    text = request.text.strip()
    if not text:
        raise AppError("CONTENT_EMPTY", "粘贴内容为空，请先输入已有论文正文或章节内容。", status_code=400)
    if len(text) > MAX_TEXT_PRECHECK_CHARS:
        raise AppError("TEXT_TOO_LONG", "粘贴正文超过当前长度限制，请改为上传 .docx。", status_code=400)
    return attach_public_export_token(run_precheck(normalize_text_input(text, CapabilityFlags())))


@router.post("/exports/docx", response_model=PublicExportResponse)
def public_export_docx(request: PublicExportDocxRequest) -> PublicExportResponse:
    digest = thesis_digest(request.thesis.model_dump_json())
    if not verify_export_token(request.export_token, digest):
        raise AppError("EXPORT_TOKEN_INVALID", "导出凭证已失效，请重新预检后再导出。", status_code=403)
    payload = export_docx(request.thesis)
    expires_at = datetime.now(UTC).replace(tzinfo=None) + timedelta(seconds=PUBLIC_EXPORT_RETENTION_SECONDS)
    export_id = f"pub_{uuid.uuid4().hex[:16]}"
    safe_title = (request.thesis.cover.title.strip() or "SC-TH-export").replace("/", "-")[:40]
    filename = f"{safe_title}.docx"
    docx_key = f"public/exports/{export_id}/{filename}"
    report_key = f"public/exports/{export_id}/self-check-report.json"
    storage.put_bytes(docx_key, payload)
    storage.put_bytes(report_key, _public_report_payload(export_id, request.thesis, expires_at))
    _write_meta(export_id, {"expires_at": expires_at.isoformat(), "docx_key": docx_key, "report_key": report_key, "filename": filename})
    return PublicExportResponse(
        export_id=export_id,
        download_url=f"/api/public/exports/{export_id}/download",
        report_url=f"/api/public/exports/{export_id}/report",
        expires_at=expires_at,
    )


@router.get("/exports/{export_id}/download")
def download_public_export(export_id: str) -> Response:
    meta = _read_valid_meta(export_id)
    payload = storage.get_bytes(meta["docx_key"])
    return Response(content=payload, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", headers={"Content-Disposition": f'attachment; filename="{meta["filename"]}"'})


@router.get("/exports/{export_id}/report")
def download_public_report(export_id: str) -> Response:
    meta = _read_valid_meta(export_id)
    return Response(content=storage.get_bytes(meta["report_key"]), media_type="application/json; charset=utf-8")


def _public_report_payload(export_id: str, thesis: NormalizedThesis, expires_at: datetime) -> bytes:
    return json.dumps(
        {
            "export_id": export_id,
            "expires_at": expires_at.isoformat(),
            "source_type": thesis.source_type,
            "manual_review_flags": thesis.manual_review_flags,
            "missing_sections": thesis.missing_sections,
        },
        ensure_ascii=False,
        indent=2,
    ).encode("utf-8")


def _meta_key(export_id: str) -> str:
    return f"public/exports/{export_id}/meta.json"


def _write_meta(export_id: str, meta: dict) -> None:
    storage.put_bytes(_meta_key(export_id), json.dumps(meta, ensure_ascii=False).encode("utf-8"))


def _read_valid_meta(export_id: str) -> dict:
    try:
        meta = json.loads(storage.get_bytes(_meta_key(export_id)).decode("utf-8"))
    except FileNotFoundError as exc:
        raise AppError("EXPORT_NOT_FOUND", "导出文件不存在或已删除。", status_code=404) from exc
    expires_at = datetime.fromisoformat(meta["expires_at"])
    if expires_at < datetime.now(UTC).replace(tzinfo=None):
        storage.delete_prefix(f"public/exports/{export_id}")
        raise AppError("EXPORT_EXPIRED", "导出文件已超过 30 分钟保留期，请重新生成。", status_code=410)
    return meta
