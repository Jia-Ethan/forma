from __future__ import annotations

import json
import logging
import re
import shutil
import subprocess
import uuid
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from pydantic import ValidationError

from .config import (
    OUTPUT_JOBS_DIR,
    TEX_REQUIRED_STYLES,
    TMP_JOBS_DIR,
    WORKING_TEMPLATE_DIR,
    ensure_runtime_dirs,
    get_extra_required_styles,
)
from .errors import AppError
from .parser import parse_docx, split_keywords
from .schemas import DocumentParseResult, GenerationArtifacts, JobStatusResponse, SectionNode, ThesisGenerationRequest

logger = logging.getLogger(__name__)


def latex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    escaped = "".join(replacements.get(ch, ch) for ch in text)
    return escaped.replace("\t", "    ")


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def now_manifest(job_id: str, source_type: str) -> dict:
    return {
        "job_id": job_id,
        "status": "queued",
        "source_type": source_type,
        "template": "latex-scnu-web",
        "warnings": [],
        "sections": [],
        "compile_command": [],
        "error_code": None,
        "error_message": None,
        "artifacts": {},
    }


def create_job(source_type: str) -> tuple[str, Path, Path, Path]:
    ensure_runtime_dirs()
    job_id = uuid.uuid4().hex[:12]
    output_dir = OUTPUT_JOBS_DIR / job_id
    tmp_dir = TMP_JOBS_DIR / job_id
    upload_dir = tmp_dir / "uploads"
    output_dir.mkdir(parents=True, exist_ok=True)
    upload_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "manifest.json"
    write_json(manifest_path, now_manifest(job_id, source_type))
    return job_id, output_dir, tmp_dir, manifest_path


def load_manifest(job_id: str) -> dict:
    manifest_path = OUTPUT_JOBS_DIR / job_id / "manifest.json"
    if not manifest_path.exists():
        raise AppError("NOT_FOUND", "任务不存在", status_code=404)
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def update_manifest(manifest_path: Path, **patch: object) -> dict:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload.update(patch)
    write_json(manifest_path, payload)
    return payload


def check_tex_environment() -> dict:
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
    return {
        "xelatex": bool(xelatex_path),
        "kpsewhich": bool(kpsewhich_path),
        "missing_styles": missing_styles,
    }


def require_tex_environment() -> None:
    status = check_tex_environment()
    if not status["xelatex"] or not status["kpsewhich"] or status["missing_styles"]:
        raise AppError(
            "TEX_ENV_MISSING",
            "本地 TeX 环境不完整，无法开始编译。",
            details=status,
            status_code=400,
        )


def normalize_text_block(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.strip().splitlines()).strip()


def render_paragraphs_as_latex(text: str) -> str:
    paragraphs = [chunk.strip() for chunk in re.split(r"\n\s*\n", normalize_text_block(text)) if chunk.strip()]
    return "\n\n".join(latex_escape(paragraph) for paragraph in paragraphs)


def render_body_from_markdown(body: str) -> str:
    normalized = normalize_text_block(body)
    if not normalized:
        raise AppError("CONTENT_EMPTY", "正文内容为空", status_code=400)

    output: list[str] = []
    saw_heading = False
    for line in normalized.splitlines():
        stripped = line.strip()
        if not stripped:
            output.append("")
            continue

        match = re.match(r"^(#{1,3})\s+(.+)$", stripped)
        if match:
            saw_heading = True
            level = len(match.group(1))
            title = latex_escape(match.group(2).strip())
            command = {1: "section", 2: "subsection", 3: "subsubsection"}[level]
            output.append(fr"\{command}{{{title}}}")
            continue

        output.append(latex_escape(stripped))

    rendered = "\n\n".join(part for part in output if part is not None).strip()
    if saw_heading:
        return rendered
    return "\\section{正文}\n\n" + rendered


def convert_sections_to_markdown(sections: list[SectionNode]) -> str:
    parts: list[str] = []
    for section in sections:
        if section.kind != "body":
            continue
        title = section.title.strip() or "正文"
        parts.append(f"# {title}")
        if section.content.strip():
            parts.append(section.content.strip())
    return "\n\n".join(parts).strip()


def extract_request_from_parse_result(parse_result: DocumentParseResult, metadata: dict[str, str]) -> ThesisGenerationRequest:
    abstract_cn = ""
    abstract_en = ""
    references = ""
    acknowledgements = ""
    appendix = ""
    body_sections: list[SectionNode] = []
    warnings = list(parse_result.warnings)

    for section in parse_result.sections:
        if section.kind == "abstract_cn" and not abstract_cn:
            abstract_cn = section.content
        elif section.kind == "abstract_en" and not abstract_en:
            abstract_en = section.content
        elif section.kind == "references":
            references = section.content
        elif section.kind == "acknowledgements":
            acknowledgements = section.content
        elif section.kind == "appendix":
            appendix = section.content
        else:
            body_sections.append(section)

    if not abstract_cn:
        warnings.append("未识别到“摘要”章节。")
    if not abstract_en:
        warnings.append("未识别到“Abstract”章节。")

    body_markdown = convert_sections_to_markdown(body_sections)
    if not body_markdown and parse_result.sections:
        raise AppError("SECTION_PARSE_FAILED", "未能从文档中识别出可用正文结构", status_code=400)

    abstract_cn, keywords_cn = split_keywords(abstract_cn, english=False)
    abstract_en, keywords_en = split_keywords(abstract_en, english=True)

    try:
        request = ThesisGenerationRequest(
            title=metadata["title"],
            author_name=metadata["author_name"],
            student_id=metadata["student_id"],
            department=metadata["department"],
            major=metadata["major"],
            class_name=metadata["class_name"],
            advisor_name=metadata["advisor_name"],
            submission_date=metadata["submission_date"],
            abstract_cn=abstract_cn,
            abstract_en=abstract_en,
            keywords_cn=keywords_cn,
            keywords_en=keywords_en,
            body=body_markdown,
            references=references,
            acknowledgements=acknowledgements,
            appendix=appendix,
        )
    except ValidationError as exc:
        raise AppError(
            "FIELD_MISSING",
            "文档缺少生成论文所需的必填字段。",
            details={"errors": exc.errors(), "warnings": warnings},
            status_code=400,
        ) from exc
    parse_result.warnings = warnings
    return request


def render_cover_tex(payload: ThesisGenerationRequest) -> str:
    title_lines = payload.title.strip()
    header_title = latex_escape(payload.title[:40])
    return f"""\\renewcommand{{\\thesistitlefancyhead}}{{{header_title}}}
\\thispagestyle{{empty}}

\\begin{{figure}}[ht]
  \\centering
  \\includegraphics[width=\\linewidth]{{./cover/scnu.jpg}}
\\end{{figure}}

\\begin{{center}}
\\zihao{{0}}
\\textbf{{本科毕业论文}}
\\end{{center}}

\\begin{{center}}
\\zihao{{1}}
\\ \\\\\\ \\\\\\ \\\\
\\end{{center}}

\\begin{{spacing}}{{1.8}}

\\begin{{table}}[ht]
  \\zihao{{-3}}
  \\centering
  \\begin{{tabular}}{{lc}}
  \\multicolumn{{1}}{{c}}{{\\textbf{{论文题目:\\ }} }} & \\textbf{{{latex_escape(title_lines)}}} \\\\ \\cline{{2-2}}
  \\multicolumn{{1}}{{c}}{{\\textbf{{指导老师:\\ }} }} & \\textbf{{{latex_escape(payload.advisor_name)}}} \\\\ \\cline{{2-2}}
  \\multicolumn{{1}}{{c}}{{\\textbf{{学生姓名:}}}}  & \\textbf{{{latex_escape(payload.author_name)}}} \\\\ \\cline{{2-2}}
  \\multicolumn{{1}}{{c}}{{\\textbf{{学\\hspace{{\\fill}}号:}}}}  & \\textbf{{{latex_escape(payload.student_id)}}} \\\\ \\cline{{2-2}}
  \\multicolumn{{1}}{{c}}{{\\textbf{{学\\hspace{{\\fill}}院:}}}}  & \\textbf{{{latex_escape(payload.department)}}} \\\\ \\cline{{2-2}}
  \\multicolumn{{1}}{{c}}{{\\textbf{{专\\hspace{{\\fill}}业:}}}}  & \\textbf{{{latex_escape(payload.major)}}} \\\\ \\cline{{2-2}}
  \\multicolumn{{1}}{{c}}{{\\textbf{{班\\hspace{{\\fill}}级:}}}}  & \\textbf{{{latex_escape(payload.class_name)}}} \\\\ \\cline{{2-2}}
  \\multicolumn{{2}}{{c}}{{\\textbf{{{latex_escape(payload.submission_date)}}}}}
  \\end{{tabular}}
\\end{{table}}

\\end{{spacing}}
\\afterpage{{\\blankpage}}
\\newpage
"""


def render_abstract_tex(title: str, heading: str, body: str, keywords_label: str, keywords: str) -> str:
    label = latex_escape(title)
    content = render_paragraphs_as_latex(body)
    keyword_line = ""
    if keywords.strip():
        keyword_line = f"\n\\ \\\\\n\\textbf{{{keywords_label}: }}{latex_escape(keywords.strip())}\n"
    return f"""\\setcounter{{page}}{{1}}
\\pagenumbering{{Roman}}
\\begin{{center}}
  \\addcontentsline{{toc}}{{section}}{{{label}}}
  \\zihao{{-2}} \\bfseries {heading}
\\end{{center}}

  \\zihao{{-4}}
{content}{keyword_line}
\\newpage
"""


def render_reference_tex(references: str) -> str:
    items = [item.strip() for item in references.splitlines() if item.strip()]
    if not items:
        return "% no references provided\n"
    rendered = ["\\zihao{-4}", "\\begin{thebibliography}{99}"]
    for index, item in enumerate(items, start=1):
        rendered.append(f"\\bibitem{{ref{index}}} {latex_escape(item)}")
    rendered.append("\\end{thebibliography}")
    rendered.append("\\newpage")
    return "\n".join(rendered) + "\n"


def render_thanks_tex(acknowledgements: str) -> str:
    body = acknowledgements.strip() or "本文暂未提供致谢内容。"
    return f"""\\section*{{致谢}}
\\addcontentsline{{toc}}{{section}}{{致谢}}
\\zihao{{-4}}

{render_paragraphs_as_latex(body)}

\\newpage
"""


def render_appendix_tex(appendix: str) -> str:
    if not appendix.strip():
        return "% no appendix provided\n"
    return f"""\\section*{{附录}}
\\addcontentsline{{toc}}{{section}}{{附录}}
\\zihao{{-4}}

{render_paragraphs_as_latex(appendix)}
"""


def render_body_files(body_markdown: str) -> dict[str, str]:
    return {"generated-body.tex": render_body_from_markdown(body_markdown) + "\n"}


def prepare_worktree(job_tmp_dir: Path) -> Path:
    work_dir = job_tmp_dir / "work"
    if work_dir.exists():
        shutil.rmtree(work_dir)
    shutil.copytree(WORKING_TEMPLATE_DIR, work_dir)
    return work_dir


def write_generated_template_files(work_dir: Path, payload: ThesisGenerationRequest) -> list[str]:
    body_files = render_body_files(payload.body)
    written_body_files: list[str] = []
    for filename, content in body_files.items():
        target = work_dir / "body" / filename
        target.write_text(content, encoding="utf-8")
        written_body_files.append(filename)

    body_index = "\n".join([f"\\input{{body/{filename.removesuffix('.tex')}}}" for filename in written_body_files]) + "\n"

    (work_dir / "cover" / "image.tex").write_text(render_cover_tex(payload), encoding="utf-8")
    (work_dir / "abstract" / "abstract-zh-CN.tex").write_text(
        render_abstract_tex("摘要", "摘\\quad 要", payload.abstract_cn, "关键词", payload.keywords_cn),
        encoding="utf-8",
    )
    (work_dir / "abstract" / "abstract-en.tex").write_text(
        render_abstract_tex("Abstract", "Abstract", payload.abstract_en, "Keywords", payload.keywords_en),
        encoding="utf-8",
    )
    (work_dir / "body" / "index.tex").write_text(body_index, encoding="utf-8")
    (work_dir / "reference" / "index.tex").write_text(render_reference_tex(payload.references), encoding="utf-8")
    (work_dir / "thanks" / "index.tex").write_text(render_thanks_tex(payload.acknowledgements), encoding="utf-8")
    (work_dir / "appendix" / "index.tex").write_text(render_appendix_tex(payload.appendix), encoding="utf-8")
    return written_body_files


def compile_worktree(work_dir: Path, compile_log_path: Path) -> list[str]:
    command = ["xelatex", "-interaction=nonstopmode", "main.tex"]
    with compile_log_path.open("w", encoding="utf-8") as log_file:
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
                raise AppError(
                    "COMPILE_FAILED",
                    "LaTeX 编译失败，请检查日志。",
                    details={"compile_log_path": str(compile_log_path)},
                    status_code=400,
                )
    return command


def zip_worktree(work_dir: Path, output_path: Path) -> None:
    try:
        with ZipFile(output_path, "w", compression=ZIP_DEFLATED) as zf:
            for file_path in work_dir.rglob("*"):
                if file_path.is_file():
                    zf.write(file_path, file_path.relative_to(work_dir))
    except Exception as exc:  # pragma: no cover - file system edge
        raise AppError(
            "ARTIFACT_WRITE_FAILED",
            "无法生成 tex 工程压缩包。",
            details={"reason": str(exc)},
            status_code=500,
        ) from exc


def build_status_response(payload: dict) -> JobStatusResponse:
    artifacts = payload.get("artifacts") or {}
    return JobStatusResponse(
        job_id=payload["job_id"],
        status=payload["status"],
        source_type=payload.get("source_type", "unknown"),
        template=payload.get("template", "latex-scnu-web"),
        error_code=payload.get("error_code"),
        error_message=payload.get("error_message"),
        warnings=payload.get("warnings") or [],
        sections=[SectionNode(**section) for section in payload.get("sections") or []],
        artifacts=GenerationArtifacts(job_id=payload["job_id"], **artifacts) if artifacts else None,
        compile_command=payload.get("compile_command") or [],
        output_dir=payload.get("output_dir"),
    )


def process_form_job(job_id: str, manifest_path: Path, output_dir: Path, tmp_dir: Path, request: ThesisGenerationRequest) -> None:
    try:
        require_tex_environment()
        update_manifest(manifest_path, status="processing")
        logger.info("job=%s source=form start", job_id)

        parse_result = DocumentParseResult(
            source_type="form",
            metadata={"title": request.title},
            sections=[SectionNode(kind="body", title="正文", content=request.body)],
            warnings=[],
        )
        artifacts = generate_from_request(job_id, output_dir, tmp_dir, request, parse_result)
        update_manifest(
            manifest_path,
            status="completed",
            sections=[section.model_dump() for section in parse_result.sections],
            warnings=parse_result.warnings,
            artifacts=artifacts,
            compile_command=artifacts["compile_command"],
            output_dir=str(output_dir),
        )
    except AppError as exc:
        update_manifest(
            manifest_path,
            status="failed",
            error_code=exc.code,
            error_message=exc.message,
            warnings=[],
            output_dir=str(output_dir),
        )
    except Exception as exc:  # pragma: no cover - catch-all for demo resilience
        update_manifest(
            manifest_path,
            status="failed",
            error_code="UNEXPECTED_ERROR",
            error_message=str(exc),
            warnings=[],
            output_dir=str(output_dir),
        )


def process_docx_job(job_id: str, manifest_path: Path, output_dir: Path, tmp_dir: Path, file_path: Path, metadata: dict[str, str]) -> None:
    try:
        require_tex_environment()
        update_manifest(manifest_path, status="processing")
        logger.info("job=%s source=docx file=%s", job_id, file_path)

        parse_result = parse_docx(file_path)
        request = extract_request_from_parse_result(parse_result, metadata)
        artifacts = generate_from_request(job_id, output_dir, tmp_dir, request, parse_result)
        update_manifest(
            manifest_path,
            status="completed",
            sections=[section.model_dump() for section in parse_result.sections],
            warnings=parse_result.warnings,
            artifacts=artifacts,
            compile_command=artifacts["compile_command"],
            output_dir=str(output_dir),
        )
    except AppError as exc:
        update_manifest(
            manifest_path,
            status="failed",
            error_code=exc.code,
            error_message=exc.message,
            warnings=exc.details.get("warnings", []),
            output_dir=str(output_dir),
        )
    except Exception as exc:  # pragma: no cover
        update_manifest(
            manifest_path,
            status="failed",
            error_code="UNEXPECTED_ERROR",
            error_message=str(exc),
            warnings=[],
            output_dir=str(output_dir),
        )


def generate_from_request(
    job_id: str,
    output_dir: Path,
    tmp_dir: Path,
    request: ThesisGenerationRequest,
    parse_result: DocumentParseResult,
) -> dict:
    work_dir = prepare_worktree(tmp_dir)
    written_body_files = write_generated_template_files(work_dir, request)

    compile_log_path = output_dir / "compile.log"
    command = compile_worktree(work_dir, compile_log_path)

    pdf_source = work_dir / "main.pdf"
    if not pdf_source.exists():
        raise AppError(
            "ARTIFACT_WRITE_FAILED",
            "编译完成后未找到 PDF 输出文件。",
            status_code=500,
        )

    pdf_output = output_dir / "thesis.pdf"
    shutil.copy2(pdf_source, pdf_output)

    texzip_output = output_dir / "tex-project.zip"
    zip_worktree(work_dir, texzip_output)

    parse_result.warnings = parse_result.warnings + [f"正文文件：{', '.join(written_body_files)}"]
    return {
        "pdf_path": str(pdf_output),
        "texzip_path": str(texzip_output),
        "compile_log_path": str(compile_log_path),
        "compile_command": command,
    }
