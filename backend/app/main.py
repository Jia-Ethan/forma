from __future__ import annotations

import io
import logging
import tempfile
from base64 import b64decode
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles

from .config import ALLOWED_DOCX_CONTENT_TYPES, ALLOWED_DOCX_EXTENSIONS, APP_ENV, CORS_ALLOWED_ORIGINS, MAX_UPLOAD_SIZE_BYTES, TEMPLATE_NAME
from .contracts import CapabilityFlags, HealthResponse, NormalizedThesis, PrecheckResponse, ServiceLimits, TextPrecheckRequest
from .errors import AppError
from .services.export import export_docx
from .services.parse import normalize_text_input, parse_docx_file
from .services.precheck import run_precheck

try:
    from .frontend_bundle import ASSETS as BUNDLED_ASSETS
    from .frontend_bundle import INDEX_HTML as BUNDLED_INDEX_HTML
except ImportError:
    # Local development can run the API before the Vite build exists.
    BUNDLED_ASSETS = {}
    BUNDLED_INDEX_HTML = None

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("scnu-thesis-portal")
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PUBLIC_DIR = PROJECT_ROOT / "public"
PUBLIC_INDEX = PUBLIC_DIR / "index.html"
PUBLIC_ASSETS = PUBLIC_DIR / "assets"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield


app = FastAPI(title="SCNU Thesis Portal", lifespan=lifespan)

if PUBLIC_ASSETS.exists():
    app.mount("/assets", StaticFiles(directory=PUBLIC_ASSETS), name="assets")

if CORS_ALLOWED_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ALLOWED_ORIGINS,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.exception_handler(AppError)
async def handle_app_error(_request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": exc.code,
            "error_message": exc.message,
            "details": exc.details,
        },
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(_request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error_code": "FIELD_MISSING",
            "error_message": "请求缺少必填字段，或字段格式不正确。",
            "details": {"errors": exc.errors()},
        },
    )


def capability_flags() -> CapabilityFlags:
    return CapabilityFlags(docx_export=True, profile="undergraduate")


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        app_env=APP_ENV,
        template=TEMPLATE_NAME,
        capabilities=capability_flags(),
        limits=ServiceLimits(max_docx_size_bytes=MAX_UPLOAD_SIZE_BYTES),
    )


@app.post("/api/precheck/docx", response_model=PrecheckResponse)
async def precheck_docx(file: UploadFile = File(...)) -> PrecheckResponse:
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

    with tempfile.TemporaryDirectory(prefix="scnu-parse-docx-") as tmp:
        upload_path = Path(tmp) / "input.docx"
        upload_path.write_bytes(payload)
        thesis = parse_docx_file(upload_path, capability_flags())
        return run_precheck(thesis)


@app.post("/api/precheck/text", response_model=PrecheckResponse)
def precheck_text(request: TextPrecheckRequest) -> PrecheckResponse:
    if not request.text.strip():
        raise AppError("CONTENT_EMPTY", "粘贴内容为空，请先输入论文正文或章节内容。", status_code=400)
    thesis = normalize_text_input(request.text, capability_flags())
    return run_precheck(thesis)


@app.post("/api/export/docx")
def export_docx_route(thesis: NormalizedThesis):
    payload = export_docx(thesis)
    return StreamingResponse(
        io.BytesIO(payload),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": 'attachment; filename="SC-TH-export.docx"'},
    )


@app.get("/assets/{asset_path:path}", include_in_schema=False)
def frontend_asset(asset_path: str) -> Response:
    bundled_asset = BUNDLED_ASSETS.get(asset_path)
    if bundled_asset:
        return Response(
            content=b64decode(bundled_asset["body_b64"]),
            media_type=bundled_asset["content_type"],
        )
    try:
        asset_file = (PUBLIC_ASSETS / asset_path).resolve()
        asset_file.relative_to(PUBLIC_ASSETS.resolve())
    except ValueError:
        raise HTTPException(status_code=404, detail="Not Found") from None
    if asset_file.exists() and asset_file.is_file():
        return FileResponse(asset_file)
    raise HTTPException(status_code=404, detail="Not Found")


def serve_spa_index() -> Response:
    if BUNDLED_INDEX_HTML:
        return Response(content=BUNDLED_INDEX_HTML, media_type="text/html")
    if not PUBLIC_INDEX.exists():
        raise HTTPException(status_code=404, detail="Frontend build not found. Run scripts/build_web_public.py first.")
    return FileResponse(PUBLIC_INDEX)


@app.get("/", include_in_schema=False)
def frontend_root() -> Response:
    return serve_spa_index()


@app.get("/{full_path:path}", include_in_schema=False)
def frontend_fallback(full_path: str) -> Response:
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not Found")
    return serve_spa_index()
