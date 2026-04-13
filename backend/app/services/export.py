from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

from ..config import DEBUG_OUTPUTS_DIR, DEBUG_PERSIST_ARTIFACTS, TEMPLATE_DOCX_PATH, TEMPLATE_NAME
from ..contracts import BodySection, NormalizedThesis
from ..errors import AppError
from .precheck import run_precheck


def normalize_text_block(text: str) -> str:
    return "\n".join(line.rstrip() for line in (text or "").strip().splitlines()).strip()


def persist_debug_copy(label: str, payload: bytes, suffix: str) -> None:
    if not DEBUG_PERSIST_ARTIFACTS:
        return
    DEBUG_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = DEBUG_OUTPUTS_DIR / f"{timestamp}-{label}.{suffix}"
    target.write_bytes(payload)


def clear_document(document: Document) -> None:
    body = document._element.body
    for child in list(body):
        if child.tag.endswith("sectPr"):
            continue
        body.remove(child)


def set_style_font(style, name: str, size: int, *, bold: bool = False) -> None:
    style.font.name = name
    style.font.size = Pt(size)
    style.font.bold = bold
    rpr = style._element.get_or_add_rPr()
    rfonts = rpr.rFonts
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    rfonts.set(qn("w:ascii"), name)
    rfonts.set(qn("w:hAnsi"), name)
    rfonts.set(qn("w:eastAsia"), name)


def set_run_font(run, name: str, size: int, *, bold: bool = False) -> None:
    run.font.name = name
    run.font.size = Pt(size)
    run.bold = bold
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.rFonts
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    rfonts.set(qn("w:ascii"), name)
    rfonts.set(qn("w:hAnsi"), name)
    rfonts.set(qn("w:eastAsia"), name)


def configure_document(document: Document) -> None:
    section = document.sections[0]
    section.top_margin = Cm(2.8)
    section.bottom_margin = Cm(2.6)
    section.left_margin = Cm(3.0)
    section.right_margin = Cm(2.6)
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)

    styles = document.styles
    set_style_font(styles["Normal"], "宋体", 12)
    set_style_font(styles["Title"], "黑体", 18, bold=True)
    set_style_font(styles["Heading 1"], "黑体", 16, bold=True)
    set_style_font(styles["Heading 2"], "黑体", 14, bold=True)
    set_style_font(styles["Heading 3"], "黑体", 13, bold=True)

    normal = styles["Normal"].paragraph_format
    normal.line_spacing = 1.5
    normal.first_line_indent = Cm(0.74)
    normal.space_after = Pt(0)


def add_centered_paragraph(document: Document, text: str, *, style: str | None = None, size: int | None = None) -> None:
    paragraph = document.add_paragraph(style=style)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run(text)
    if size:
        set_run_font(run, "黑体", size, bold=style == "Title")


def add_page_break(document: Document) -> None:
    document.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def add_cover_page(document: Document, thesis: NormalizedThesis) -> None:
    meta = thesis.metadata
    add_centered_paragraph(document, "华南师范大学", style="Title")
    add_centered_paragraph(document, "本科毕业论文", size=18)
    document.add_paragraph()
    add_centered_paragraph(document, meta.title.strip() or "待补充论文题目", size=20)
    document.add_paragraph()

    table = document.add_table(rows=7, cols=2)
    table.style = "Table Grid"
    rows = [
        ("学生姓名", meta.author_name or "未填写"),
        ("学号", meta.student_id or "未填写"),
        ("学院", meta.department or "未填写"),
        ("专业", meta.major or "未填写"),
        ("班级", meta.class_name or "未填写"),
        ("指导老师", meta.advisor_name or "未填写"),
        ("提交日期", meta.submission_date or "未填写"),
    ]
    for row, values in zip(table.rows, rows):
        row.cells[0].text = values[0]
        row.cells[1].text = values[1]

    add_page_break(document)


def add_toc(document: Document) -> None:
    heading = document.add_paragraph(style="Heading 1")
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    heading.add_run("目录")

    paragraph = document.add_paragraph()
    run = paragraph.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr_text = OxmlElement("w:instrText")
    instr_text.set(qn("xml:space"), "preserve")
    instr_text.text = 'TOC \\o "1-3" \\h \\z \\u'
    fld_separate = OxmlElement("w:fldChar")
    fld_separate.set(qn("w:fldCharType"), "separate")
    placeholder = OxmlElement("w:t")
    placeholder.text = "请在 Word 中右键更新目录。"
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.extend([fld_begin, instr_text, fld_separate, placeholder, fld_end])
    add_page_break(document)


def add_heading(document: Document, text: str, level: int = 1, *, center: bool = False) -> None:
    paragraph = document.add_paragraph(style=f"Heading {min(max(level, 1), 3)}")
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER if center else WD_ALIGN_PARAGRAPH.LEFT
    paragraph.add_run(text)


def add_paragraphs(document: Document, text: str) -> None:
    normalized = normalize_text_block(text)
    if not normalized:
        return
    for chunk in [item.strip() for item in normalized.split("\n\n") if item.strip()]:
        document.add_paragraph(chunk)


def add_summary_section(document: Document, heading: str, content: str, keywords_label: str, keywords: list[str]) -> None:
    add_heading(document, heading, 1, center=True)
    add_paragraphs(document, content)
    if keywords:
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.add_run(f"{keywords_label}：").bold = True
        paragraph.add_run("；".join(keywords))
    add_page_break(document)


def add_body_section(document: Document, section: BodySection) -> None:
    add_heading(document, section.title.strip() or "正文", section.level)
    add_paragraphs(document, section.content)


def add_references(document: Document, items: list[str]) -> None:
    add_heading(document, "参考文献", 1)
    for index, item in enumerate(items, start=1):
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.add_run(f"[{index}] {item}")


def add_simple_section(document: Document, heading: str, text: str) -> None:
    if not normalize_text_block(text):
        return
    add_page_break(document)
    add_heading(document, heading, 1)
    add_paragraphs(document, text)


def load_template_document() -> Document:
    if not TEMPLATE_DOCX_PATH.exists():
        raise AppError(
            "TEMPLATE_DEPENDENCY_MISSING",
            "Word 模板不存在，无法生成导出结果。",
            details={"template": str(TEMPLATE_DOCX_PATH)},
            status_code=500,
        )
    try:
        document = Document(TEMPLATE_DOCX_PATH)
    except Exception as exc:  # pragma: no cover
        raise AppError(
            "TEMPLATE_DEPENDENCY_MISSING",
            "Word 模板无法加载，请检查模板文件是否损坏。",
            details={"template": str(TEMPLATE_DOCX_PATH), "reason": str(exc)},
            status_code=500,
        ) from exc

    clear_document(document)
    configure_document(document)
    return document


def validate_for_export(thesis: NormalizedThesis) -> None:
    precheck = run_precheck(thesis)
    if precheck.summary.blocking_count > 0:
        raise AppError(
            "FIELD_MISSING",
            "预检仍存在阻塞项，无法导出 Word 文件。",
            details={
                "blocking_count": precheck.summary.blocking_count,
                "issues": [issue.model_dump() for issue in precheck.issues if issue.severity == "blocking"],
            },
            status_code=400,
        )


def export_docx(thesis: NormalizedThesis) -> bytes:
    validate_for_export(thesis)

    try:
        document = load_template_document()
        add_cover_page(document, thesis)
        add_toc(document)
        add_summary_section(document, "摘要", thesis.abstract_cn.content, "关键词", thesis.abstract_cn.keywords)

        if normalize_text_block(thesis.abstract_en.content):
            add_summary_section(document, "Abstract", thesis.abstract_en.content, "Keywords", thesis.abstract_en.keywords)

        for index, section in enumerate(thesis.body_sections):
            if index == 0:
                add_heading(document, section.title.strip() or "正文", section.level)
                add_paragraphs(document, section.content)
            else:
                add_body_section(document, section)

        add_page_break(document)
        add_references(document, thesis.references.items)
        add_simple_section(document, "致谢", thesis.acknowledgements)
        add_simple_section(document, "附录", thesis.appendix)

        buffer = io.BytesIO()
        document.save(buffer)
        payload = buffer.getvalue()
        persist_debug_copy("word-thesis", payload, "docx")
        return payload
    except AppError:
        raise
    except Exception as exc:  # pragma: no cover
        raise AppError("EXPORT_FAILED", "导出 Word 文件失败，请稍后重试。", details={"reason": str(exc)}, status_code=500) from exc
