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

from .config import ALLOWED_DOCX_EXTENSIONS, APP_ENV, ENABLE_PDF_EXPORT, MAX_UPLOAD_SIZE_BYTES, TEMPLATE_NAME
from .contracts import CapabilityFlags, HealthResponse, NormalizedThesis, ServiceLimits, TextNormalizeRequest
from .errors import AppError
from .services.export import export_texzip
from .services.parse import normalize_text_input, parse_docx_file
from .services.pdf import check_tex_environment, export_pdf

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


@app.get("/assets/{asset_path:path}", include_in_schema=False)
def frontend_asset(asset_path: str) -> Response:
    bundled_asset = BUNDLED_ASSETS.get(asset_path)
    if bundled_asset:
        return Response(
            content=b64decode(bundled_asset["body_b64"]),
            media_type=bundled_asset["content_type"],
        )
    asset_file = PUBLIC_ASSETS / asset_path
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
