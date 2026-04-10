from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = PROJECT_ROOT / "web"
PUBLIC_DIR = PROJECT_ROOT / "public"
TEMPLATES_ROOT = PROJECT_ROOT / "templates"
WORKING_TEMPLATE_DIR = TEMPLATES_ROOT / "working" / "latex-scnu-web"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
DEBUG_OUTPUTS_DIR = OUTPUTS_DIR / "debug"

ALLOWED_DOCX_EXTENSIONS = {".docx"}
APP_ENV = os.getenv("APP_ENV", "development").strip().lower() or "development"
TEMPLATE_NAME = "latex-scnu-web"


def read_bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


MAX_UPLOAD_SIZE_BYTES = int(os.getenv("MAX_DOCX_SIZE_BYTES", str(4 * 1024 * 1024)))
ENABLE_PDF_EXPORT = read_bool_env("ENABLE_PDF_EXPORT", APP_ENV != "production")
DEBUG_PERSIST_ARTIFACTS = read_bool_env("SCNU_DEBUG_PERSIST_ARTIFACTS", False)

TEX_REQUIRED_STYLES = [
    "ctex.sty",
    "titlesec.sty",
    "titletoc.sty",
]


def get_extra_required_styles() -> list[str]:
    raw = os.getenv("SCNU_EXTRA_REQUIRED_STYLES", "")
    return [item.strip() for item in raw.split(",") if item.strip()]
