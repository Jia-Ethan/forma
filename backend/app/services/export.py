from __future__ import annotations

import io
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from ..config import DEBUG_OUTPUTS_DIR, DEBUG_PERSIST_ARTIFACTS, TEMPLATE_NAME, WORKING_TEMPLATE_DIR
from ..contracts import BodySection, NormalizedThesis
from ..errors import AppError


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


def normalize_text_block(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.strip().splitlines()).strip()


def render_paragraphs_as_latex(text: str) -> str:
    paragraphs = [chunk.strip() for chunk in normalize_text_block(text).split("\n\n") if chunk.strip()]
    return "\n\n".join(latex_escape(paragraph) for paragraph in paragraphs)


def render_body_sections(body_sections: list[BodySection]) -> str:
    if not body_sections:
        raise AppError("CONTENT_EMPTY", "正文内容为空，无法导出。", status_code=400)

    commands = {1: "section", 2: "subsection", 3: "subsubsection"}
    parts: list[str] = []
    for section in body_sections:
        level = min(max(section.level, 1), 3)
        title = latex_escape(section.title.strip() or "正文")
        parts.append(f"\\{commands[level]}{{{title}}}")
        if section.content.strip():
            parts.append(render_paragraphs_as_latex(section.content))
    return "\n\n".join(parts).strip() + "\n"


def render_cover_tex(thesis: NormalizedThesis) -> str:
    metadata = thesis.metadata
    header_title = latex_escape((metadata.title or "论文题目")[:40])
    title = latex_escape(metadata.title or "待补充论文题目")
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
  \\multicolumn{{1}}{{c}}{{\\textbf{{论文题目:\\ }} }} & \\textbf{{{title}}} \\\\ \\cline{{2-2}}
  \\multicolumn{{1}}{{c}}{{\\textbf{{指导老师:\\ }} }} & \\textbf{{{latex_escape(metadata.advisor_name)}}} \\\\ \\cline{{2-2}}
  \\multicolumn{{1}}{{c}}{{\\textbf{{学生姓名:}}}}  & \\textbf{{{latex_escape(metadata.author_name)}}} \\\\ \\cline{{2-2}}
  \\multicolumn{{1}}{{c}}{{\\textbf{{学\\hspace{{\\fill}}号:}}}}  & \\textbf{{{latex_escape(metadata.student_id)}}} \\\\ \\cline{{2-2}}
  \\multicolumn{{1}}{{c}}{{\\textbf{{学\\hspace{{\\fill}}院:}}}}  & \\textbf{{{latex_escape(metadata.department)}}} \\\\ \\cline{{2-2}}
  \\multicolumn{{1}}{{c}}{{\\textbf{{专\\hspace{{\\fill}}业:}}}}  & \\textbf{{{latex_escape(metadata.major)}}} \\\\ \\cline{{2-2}}
  \\multicolumn{{1}}{{c}}{{\\textbf{{班\\hspace{{\\fill}}级:}}}}  & \\textbf{{{latex_escape(metadata.class_name)}}} \\\\ \\cline{{2-2}}
  \\multicolumn{{2}}{{c}}{{\\textbf{{{latex_escape(metadata.submission_date)}}}}}
  \\end{{tabular}}
\\end{{table}}

\\end{{spacing}}
\\afterpage{{\\blankpage}}
\\newpage
"""


def render_abstract_tex(title: str, heading: str, content: str, keywords_label: str, keywords: list[str]) -> str:
    rendered = render_paragraphs_as_latex(content)
    keywords_line = ""
    if keywords:
        keywords_line = f"\n\\ \\\\\n\\textbf{{{keywords_label}: }}{latex_escape('；'.join(keywords))}\n"
    return f"""\\setcounter{{page}}{{1}}
\\pagenumbering{{Roman}}
\\begin{{center}}
  \\addcontentsline{{toc}}{{section}}{{{latex_escape(title)}}}
  \\zihao{{-2}} \\bfseries {heading}
\\end{{center}}

  \\zihao{{-4}}
{rendered}{keywords_line}
\\newpage
"""


def render_reference_tex(items: list[str]) -> str:
    if not items:
        return "% no references provided\n"
    lines = ["\\zihao{-4}", "\\begin{thebibliography}{99}"]
    for index, item in enumerate(items, start=1):
        lines.append(f"\\bibitem{{ref{index}}} {latex_escape(item)}")
    lines.extend(["\\end{thebibliography}", "\\newpage"])
    return "\n".join(lines) + "\n"


def render_thanks_tex(text: str) -> str:
    body = text.strip() or "本文暂未提供致谢内容。"
    return f"""\\section*{{致谢}}
\\addcontentsline{{toc}}{{section}}{{致谢}}
\\zihao{{-4}}

{render_paragraphs_as_latex(body)}

\\newpage
"""


def render_appendix_tex(text: str) -> str:
    if not text.strip():
        return "% no appendix provided\n"
    return f"""\\section*{{附录}}
\\addcontentsline{{toc}}{{section}}{{附录}}
\\zihao{{-4}}

{render_paragraphs_as_latex(text)}
"""


def validate_for_export(thesis: NormalizedThesis) -> None:
    metadata = thesis.metadata
    missing_fields: list[str] = []
    required_metadata_fields = {
        "title",
        "author_name",
        "student_id",
        "department",
        "major",
        "advisor_name",
        "submission_date",
    }

    for field_name, value in metadata.model_dump().items():
        if field_name in required_metadata_fields and (not value or not str(value).strip()):
            missing_fields.append(field_name)

    if not thesis.abstract_cn.content.strip():
        if not missing_fields and thesis.abstract_en.content.strip() and thesis.body_sections:
            raise AppError("ABSTRACT_CN_MISSING", "中文摘要为空，请先补全后再导出。", status_code=400)
        missing_fields.append("abstract_cn.content")

    if not thesis.abstract_en.content.strip():
        if not missing_fields and thesis.abstract_cn.content.strip() and thesis.body_sections:
            raise AppError("ABSTRACT_EN_MISSING", "英文 Abstract 为空，请先补全后再导出。", status_code=400)
        missing_fields.append("abstract_en.content")

    if not thesis.body_sections:
        missing_fields.append("body_sections")

    if missing_fields:
        raise AppError(
            "FIELD_MISSING",
            "导出前仍有必填字段缺失，请先补全。",
            details={"missing_fields": missing_fields},
            status_code=400,
        )


def prepare_worktree(target_dir: Path) -> Path:
    if not WORKING_TEMPLATE_DIR.exists():
        raise AppError(
            "TEMPLATE_DEPENDENCY_MISSING",
            "工作模板不存在，无法生成导出结果。",
            details={"template_dir": str(WORKING_TEMPLATE_DIR)},
            status_code=500,
        )

    work_dir = target_dir / TEMPLATE_NAME
    shutil.copytree(WORKING_TEMPLATE_DIR, work_dir)
    return work_dir


def safe_relative_path(file_path: Path, root: Path) -> Path:
    try:
        return file_path.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise AppError("EXPORT_FAILED", "导出 tex 工程失败：发现不安全的模板路径。", status_code=500) from exc


def write_generated_files(work_dir: Path, thesis: NormalizedThesis) -> None:
    (work_dir / "cover" / "image.tex").write_text(render_cover_tex(thesis), encoding="utf-8")
    (work_dir / "abstract" / "abstract-zh-CN.tex").write_text(
        render_abstract_tex("摘要", "摘\\quad 要", thesis.abstract_cn.content, "关键词", thesis.abstract_cn.keywords),
        encoding="utf-8",
    )
    (work_dir / "abstract" / "abstract-en.tex").write_text(
        render_abstract_tex("Abstract", "Abstract", thesis.abstract_en.content, "Keywords", thesis.abstract_en.keywords),
        encoding="utf-8",
    )
    (work_dir / "body" / "generated-body.tex").write_text(render_body_sections(thesis.body_sections), encoding="utf-8")
    (work_dir / "body" / "index.tex").write_text("\\input{body/generated-body}\n", encoding="utf-8")
    (work_dir / "reference" / "index.tex").write_text(render_reference_tex(thesis.references.items), encoding="utf-8")
    (work_dir / "thanks" / "index.tex").write_text(render_thanks_tex(thesis.acknowledgements), encoding="utf-8")
    (work_dir / "appendix" / "index.tex").write_text(render_appendix_tex(thesis.appendix), encoding="utf-8")


def zip_worktree_bytes(work_dir: Path) -> bytes:
    buffer = io.BytesIO()
    with ZipFile(buffer, "w", compression=ZIP_DEFLATED) as zf:
        for file_path in sorted(work_dir.rglob("*")):
            if file_path.is_symlink():
                continue
            if file_path.is_file():
                zf.write(file_path, safe_relative_path(file_path, work_dir))
    return buffer.getvalue()


def persist_debug_copy(label: str, payload: bytes, suffix: str) -> None:
    if not DEBUG_PERSIST_ARTIFACTS:
        return
    DEBUG_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = DEBUG_OUTPUTS_DIR / f"{timestamp}-{label}.{suffix}"
    target.write_bytes(payload)


def export_texzip(thesis: NormalizedThesis) -> bytes:
    validate_for_export(thesis)
    try:
        with tempfile.TemporaryDirectory(prefix="scnu-texzip-") as tmp:
            work_dir = prepare_worktree(Path(tmp))
            write_generated_files(work_dir, thesis)
            payload = zip_worktree_bytes(work_dir)
            persist_debug_copy("tex-project", payload, "zip")
            return payload
    except AppError:
        raise
    except Exception as exc:  # pragma: no cover
        raise AppError("EXPORT_FAILED", "导出 tex 工程失败。", details={"reason": str(exc)}, status_code=500) from exc
