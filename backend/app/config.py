from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
WEB_ROOT = PROJECT_ROOT / "web"
WEB_DIST_DIR = WEB_ROOT / "dist"
TEMPLATES_ROOT = PROJECT_ROOT / "templates"
WORKING_TEMPLATE_DIR = TEMPLATES_ROOT / "working" / "latex-scnu-web"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
OUTPUT_JOBS_DIR = OUTPUTS_DIR / "jobs"
TMP_DIR = PROJECT_ROOT / "tmp"
TMP_JOBS_DIR = TMP_DIR / "jobs"
EXAMPLES_DIR = PROJECT_ROOT / "examples"

ALLOWED_DOCX_EXTENSIONS = {".docx"}
MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024

TEX_REQUIRED_STYLES = [
    "ctex.sty",
    "titlesec.sty",
    "titletoc.sty",
]


def get_extra_required_styles() -> list[str]:
    raw = os.getenv("SCNU_EXTRA_REQUIRED_STYLES", "")
    return [item.strip() for item in raw.split(",") if item.strip()]


def ensure_runtime_dirs() -> None:
    for path in (
        OUTPUTS_DIR,
        OUTPUT_JOBS_DIR,
        TMP_DIR,
        TMP_JOBS_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)
