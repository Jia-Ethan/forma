from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = PROJECT_ROOT / "web"
PUBLIC_DIR = PROJECT_ROOT / "public"
TEMPLATES_ROOT = PROJECT_ROOT / "templates"
WORKING_TEMPLATE_DIR = TEMPLATES_ROOT / "working" / "sc-th-word"
TEMPLATE_DOCX_PATH = WORKING_TEMPLATE_DIR / "template.docx"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
DEBUG_OUTPUTS_DIR = OUTPUTS_DIR / "debug"

ALLOWED_DOCX_EXTENSIONS = {".docx"}
ALLOWED_DOCX_CONTENT_TYPES = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/octet-stream",
    "application/zip",
    "",
}
APP_ENV = os.getenv("APP_ENV", "development").strip().lower() or "development"
TEMPLATE_NAME = "sc-th-word"


def read_bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def read_int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value > 0 else default


def read_csv_env(name: str, default: list[str]) -> list[str]:
    raw = os.getenv(name)
    if raw is None:
        return default
    return [item.strip() for item in raw.split(",") if item.strip()]


MAX_UPLOAD_SIZE_BYTES = read_int_env("MAX_DOCX_SIZE_BYTES", 4 * 1024 * 1024)
DEBUG_PERSIST_ARTIFACTS = read_bool_env("SCNU_DEBUG_PERSIST_ARTIFACTS", False)
CORS_ALLOWED_ORIGINS = read_csv_env(
    "CORS_ALLOWED_ORIGINS",
    ["http://127.0.0.1:5173", "http://localhost:5173"] if APP_ENV != "production" else [],
)
