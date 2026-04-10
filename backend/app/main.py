from __future__ import annotations

import logging
import threading
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import ALLOWED_DOCX_EXTENSIONS, MAX_UPLOAD_SIZE_BYTES, OUTPUT_JOBS_DIR, TMP_JOBS_DIR, WEB_DIST_DIR, ensure_runtime_dirs
from .errors import AppError
from .generator import (
    build_status_response,
    check_tex_environment,
    create_job,
    load_manifest,
    process_docx_job,
    process_form_job,
)
from .schemas import JobCreateResponse, JobStatusResponse, ThesisGenerationRequest

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("scnu-thesis-portal")

app = FastAPI(title="SCNU Thesis Portal Local MVP")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    ensure_runtime_dirs()


def job_thread(target, *args) -> None:
    thread = threading.Thread(target=target, args=args, daemon=True)
    thread.start()


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


@app.get("/api/health")
def health() -> dict:
    tex_status = check_tex_environment()
    return {"ok": True, "tex": tex_status}


@app.post("/api/jobs/from-form", response_model=JobCreateResponse)
def create_job_from_form(request: ThesisGenerationRequest) -> JobCreateResponse:
    job_id, output_dir, tmp_dir, manifest_path = create_job("form")
    job_thread(process_form_job, job_id, manifest_path, output_dir, tmp_dir, request)
    return JobCreateResponse(job_id=job_id, status="queued")


@app.post("/api/jobs/from-docx", response_model=JobCreateResponse)
async def create_job_from_docx(
    file: UploadFile = File(...),
    title: str = Form(...),
    author_name: str = Form(...),
    student_id: str = Form(...),
    department: str = Form(...),
    major: str = Form(...),
    class_name: str = Form(...),
    advisor_name: str = Form(...),
    submission_date: str = Form(...),
) -> JobCreateResponse:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_DOCX_EXTENSIONS:
        raise AppError("DOCX_INVALID", "仅支持上传 .docx 文件", status_code=400)

    payload = await file.read()
    if not payload:
        raise AppError("CONTENT_EMPTY", "上传文件为空", status_code=400)
    if len(payload) > MAX_UPLOAD_SIZE_BYTES:
        raise AppError("DOCX_INVALID", "上传文件过大", status_code=400)

    job_id, output_dir, tmp_dir, manifest_path = create_job("docx")
    upload_path = tmp_dir / "uploads" / "input.docx"
    upload_path.write_bytes(payload)
    metadata = {
        "title": title.strip(),
        "author_name": author_name.strip(),
        "student_id": student_id.strip(),
        "department": department.strip(),
        "major": major.strip(),
        "class_name": class_name.strip(),
        "advisor_name": advisor_name.strip(),
        "submission_date": submission_date.strip(),
    }
    job_thread(process_docx_job, job_id, manifest_path, output_dir, tmp_dir, upload_path, metadata)
    return JobCreateResponse(job_id=job_id, status="queued")


@app.get("/api/jobs/{job_id}", response_model=JobStatusResponse)
def get_job(job_id: str) -> JobStatusResponse:
    manifest = load_manifest(job_id)
    return build_status_response(manifest)


@app.get("/api/jobs/{job_id}/artifacts/pdf")
def download_pdf(job_id: str):
    manifest = load_manifest(job_id)
    pdf_path = manifest.get("artifacts", {}).get("pdf_path")
    if not pdf_path or not Path(pdf_path).exists():
        raise HTTPException(status_code=404, detail="PDF 不存在")
    return FileResponse(pdf_path, media_type="application/pdf", filename=f"{job_id}.pdf")


@app.get("/api/jobs/{job_id}/artifacts/texzip")
def download_texzip(job_id: str):
    manifest = load_manifest(job_id)
    texzip_path = manifest.get("artifacts", {}).get("texzip_path")
    if not texzip_path or not Path(texzip_path).exists():
        raise HTTPException(status_code=404, detail="tex 工程压缩包不存在")
    return FileResponse(texzip_path, media_type="application/zip", filename=f"{job_id}.zip")


if WEB_DIST_DIR.exists():
    assets_dir = WEB_DIST_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/", include_in_schema=False)
    def serve_index():
        return FileResponse(WEB_DIST_DIR / "index.html")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_spa(full_path: str):
        candidate = WEB_DIST_DIR / full_path
        if candidate.exists() and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(WEB_DIST_DIR / "index.html")
else:
    @app.get("/", include_in_schema=False)
    def root_placeholder():
        return {
            "message": "前端尚未构建。开发模式请启动 Vite，演示模式请先执行 npm run build。"
        }
