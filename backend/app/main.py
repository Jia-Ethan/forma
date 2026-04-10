from __future__ import annotations

import io
import logging
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from .config import ALLOWED_DOCX_EXTENSIONS, APP_ENV, ENABLE_PDF_EXPORT, MAX_UPLOAD_SIZE_BYTES, TEMPLATE_NAME
from .contracts import CapabilityFlags, HealthResponse, NormalizedThesis, ServiceLimits, TextNormalizeRequest
from .errors import AppError
from .services.export import export_texzip
from .services.parse import normalize_text_input, parse_docx_file
from .services.pdf import check_tex_environment, export_pdf

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("scnu-thesis-portal")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield


app = FastAPI(title="SCNU Thesis Portal", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
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
    tex_status = check_tex_environment()
    if ENABLE_PDF_EXPORT and tex_status.xelatex and tex_status.kpsewhich and not tex_status.missing_styles:
        return CapabilityFlags(tex_zip=True, pdf=True, pdf_reason=None)
    if ENABLE_PDF_EXPORT:
        return CapabilityFlags(tex_zip=True, pdf=False, pdf_reason="本地 TeX 依赖缺失，暂不可导出 PDF。")
    return CapabilityFlags(tex_zip=True, pdf=False, pdf_reason="生产环境默认关闭 PDF，请导出 tex 工程 zip。")


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        app_env=APP_ENV,
        template=TEMPLATE_NAME,
        capabilities=capability_flags(),
        limits=ServiceLimits(max_docx_size_bytes=MAX_UPLOAD_SIZE_BYTES),
        tex=check_tex_environment(),
    )


@app.post("/api/parse/docx", response_model=NormalizedThesis)
async def parse_docx(file: UploadFile = File(...)) -> NormalizedThesis:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_DOCX_EXTENSIONS:
        raise AppError("UNSUPPORTED_FILE_TYPE", "仅支持上传 .docx 文件", status_code=400)

    payload = await file.read()
    if not payload:
        raise AppError("CONTENT_EMPTY", "上传文件为空", status_code=400)
    if len(payload) > MAX_UPLOAD_SIZE_BYTES:
        raise AppError("DOCX_INVALID", "上传文件过大", status_code=400)

    with tempfile.TemporaryDirectory(prefix="scnu-parse-docx-") as tmp:
        upload_path = Path(tmp) / "input.docx"
        upload_path.write_bytes(payload)
        return parse_docx_file(upload_path, capability_flags())


@app.post("/api/normalize/text", response_model=NormalizedThesis)
def normalize_text(request: TextNormalizeRequest) -> NormalizedThesis:
    return normalize_text_input(request.text, capability_flags())


@app.post("/api/export/texzip")
def export_texzip_route(thesis: NormalizedThesis):
    payload = export_texzip(thesis)
    return StreamingResponse(
        io.BytesIO(payload),
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="scnu-thesis.zip"'},
    )


@app.post("/api/export/pdf")
def export_pdf_route(thesis: NormalizedThesis):
    payload = export_pdf(thesis)
    return StreamingResponse(
        io.BytesIO(payload),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="scnu-thesis.pdf"'},
    )


@app.get("/", include_in_schema=False)
def root_placeholder():
    return {
        "message": "SCNU Thesis Portal API is running.",
        "app_env": APP_ENV,
        "template": TEMPLATE_NAME,
    }
