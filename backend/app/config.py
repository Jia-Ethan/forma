from __future__ import annotations

import os
from hashlib import sha256
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = PROJECT_ROOT / "web"
PUBLIC_DIR = PROJECT_ROOT / "public"
TEMPLATES_ROOT = PROJECT_ROOT / "templates"
WORKING_TEMPLATE_DIR = TEMPLATES_ROOT / "working" / "sc-th-word"
TEMPLATE_DOCX_PATH = WORKING_TEMPLATE_DIR / "template.docx"
WORKING_ASSETS_DIR = WORKING_TEMPLATE_DIR / "assets"
COVER_LOGO_PATH = WORKING_ASSETS_DIR / "scnu-cover-logo.jpg"
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


ACCESS_CODE_COOKIE_NAME = "scnu_access_token"


def access_code() -> str:
    return os.getenv("SCNU_ACCESS_CODE", "").strip()


def secret_key() -> str:
    configured = os.getenv("SCNU_SECRET_KEY", "").strip()
    if configured:
        return configured
    seed = f"insecure-local-dev-key:{PROJECT_ROOT}:{APP_ENV}"
    return sha256(seed.encode("utf-8")).hexdigest()


def using_insecure_local_secret() -> bool:
    return not bool(os.getenv("SCNU_SECRET_KEY", "").strip())
