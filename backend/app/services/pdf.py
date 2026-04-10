from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from ..config import DEBUG_OUTPUTS_DIR, DEBUG_PERSIST_ARTIFACTS, ENABLE_PDF_EXPORT, TEX_REQUIRED_STYLES, get_extra_required_styles
from ..contracts import NormalizedThesis, TeXDependencyStatus
from ..errors import AppError
from .export import persist_debug_copy, prepare_worktree, validate_for_export, write_generated_files


def check_tex_environment() -> TeXDependencyStatus:
    xelatex_path = shutil.which("xelatex")
    kpsewhich_path = shutil.which("kpsewhich")
    missing_styles: list[str] = []
    styles_to_check = TEX_REQUIRED_STYLES + get_extra_required_styles()
    if xelatex_path and kpsewhich_path:
        for style in styles_to_check:
            result = subprocess.run(
                [kpsewhich_path, style],
                capture_output=True,
                text=True,
                check=False,
            )
            if not result.stdout.strip():
                missing_styles.append(style)
    else:
        missing_styles.extend(styles_to_check)
    return TeXDependencyStatus(
        xelatex=bool(xelatex_path),
        kpsewhich=bool(kpsewhich_path),
        missing_styles=missing_styles,
    )


def require_pdf_enabled() -> None:
    if not ENABLE_PDF_EXPORT:
        raise AppError("PDF_DISABLED", "当前环境未开启 PDF 导出，请使用 tex 工程 zip。", status_code=400)


def require_tex_environment() -> None:
    status = check_tex_environment()
    if not status.xelatex or not status.kpsewhich or status.missing_styles:
        raise AppError(
            "TEMPLATE_DEPENDENCY_MISSING",
            "本地 TeX 环境不完整，无法生成 PDF。",
            details=status.model_dump(),
            status_code=400,
        )


def export_pdf(thesis: NormalizedThesis) -> bytes:
    require_pdf_enabled()
    require_tex_environment()
    validate_for_export(thesis)

    try:
        with tempfile.TemporaryDirectory(prefix="scnu-pdf-") as tmp:
            work_dir = prepare_worktree(Path(tmp))
            write_generated_files(work_dir, thesis)
            compile_log = work_dir / "compile.log"
            command = ["xelatex", "-interaction=nonstopmode", "main.tex"]
            with compile_log.open("w", encoding="utf-8") as log_file:
                for pass_index in range(2):
                    log_file.write(f"== pass {pass_index + 1} ==\n")
                    process = subprocess.run(
                        command,
                        cwd=work_dir,
                        stdout=log_file,
                        stderr=subprocess.STDOUT,
                        text=True,
                        check=False,
                    )
                    log_file.write(f"\n[exit_code] {process.returncode}\n")
                    if process.returncode != 0:
                        if DEBUG_PERSIST_ARTIFACTS:
                            DEBUG_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(compile_log, DEBUG_OUTPUTS_DIR / "compile.log")
                        raise AppError(
                            "EXPORT_FAILED",
                            "PDF 编译失败，请检查本地 TeX 依赖与日志。",
                            details={"compile_log": str(compile_log)},
                            status_code=400,
                        )

            pdf_path = work_dir / "main.pdf"
            if not pdf_path.exists():
                raise AppError("EXPORT_FAILED", "编译完成后未找到 PDF 文件。", status_code=500)

            payload = pdf_path.read_bytes()
            persist_debug_copy("thesis", payload, "pdf")
            return payload
    except AppError:
        raise
    except Exception as exc:  # pragma: no cover
        raise AppError("EXPORT_FAILED", "导出 PDF 失败。", details={"reason": str(exc)}, status_code=500) from exc
