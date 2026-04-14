from __future__ import annotations

import io
import re
from datetime import datetime

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

from ..config import DEBUG_OUTPUTS_DIR, DEBUG_PERSIST_ARTIFACTS, TEMPLATE_DOCX_PATH
from ..contracts import BodySection, NormalizedThesis
from ..errors import AppError
from .precheck import run_precheck

A4_WIDTH_CM = 21
A4_HEIGHT_CM = 29.7
BODY_FONT_SIZE = 12
SMALL_SECOND_FONT_SIZE = 18
FOURTH_FONT_SIZE = 14
FIFTH_FONT_SIZE = 10.5
BODY_LINE_SPACING = 1.25
BODY_FIRST_LINE_INDENT = Pt(24)

STYLE_BASE_FONTS = {
    "cn_heading": "黑体",
    "cn_body": "宋体",
    "latin": "Times New Roman",
}

STYLE_IDS = {name: f"SCTH{name}" for name in [
    "ThesisTitle",
    "ChineseAbstractHeading",
    "ChineseAbstractBody",
    "EnglishAbstractHeading",
    "EnglishAbstractBody",
    "KeywordsLabel",
    "TOCHeading",
    "Heading1",
    "Heading2",
    "Heading3",
    "Heading4",
    "BodyText",
    "ReferenceHeading",
    "ReferenceEntry",
    "AppendixHeading",
    "AppendixItemHeading",
    "AcknowledgementHeading",
    "NoteText",
]}

STYLE_SPECS = {
    "ThesisTitle": {
        "font_east_asia": "黑体",
        "font_ascii": "Times New Roman",
        "size": 16,
        "bold": True,
        "alignment": WD_ALIGN_PARAGRAPH.CENTER,
        "space_after": Pt(12),
    },
    "ChineseAbstractHeading": {
        "font_east_asia": "黑体",
        "font_ascii": "Times New Roman",
        "size": SMALL_SECOND_FONT_SIZE,
        "bold": True,
        "alignment": WD_ALIGN_PARAGRAPH.CENTER,
        "space_after": Pt(12),
    },
    "ChineseAbstractBody": {
        "font_east_asia": "宋体",
        "font_ascii": "Times New Roman",
        "size": BODY_FONT_SIZE,
        "line_spacing": BODY_LINE_SPACING,
        "first_line_indent": BODY_FIRST_LINE_INDENT,
    },
    "EnglishAbstractHeading": {
        "font_east_asia": "黑体",
        "font_ascii": "Times New Roman",
        "size": SMALL_SECOND_FONT_SIZE,
        "bold": True,
        "alignment": WD_ALIGN_PARAGRAPH.CENTER,
        "space_after": Pt(12),
    },
    "EnglishAbstractBody": {
        "font_east_asia": "Times New Roman",
        "font_ascii": "Times New Roman",
        "size": BODY_FONT_SIZE,
        "line_spacing": BODY_LINE_SPACING,
        "first_line_indent": BODY_FIRST_LINE_INDENT,
    },
    "KeywordsLabel": {
        "font_east_asia": "宋体",
        "font_ascii": "Times New Roman",
        "size": BODY_FONT_SIZE,
        "line_spacing": BODY_LINE_SPACING,
        "first_line_indent": BODY_FIRST_LINE_INDENT,
    },
    "TOCHeading": {
        "font_east_asia": "黑体",
        "font_ascii": "Times New Roman",
        "size": SMALL_SECOND_FONT_SIZE,
        "bold": True,
        "alignment": WD_ALIGN_PARAGRAPH.CENTER,
        "space_after": Pt(12),
    },
    "Heading1": {
        "font_east_asia": "黑体",
        "font_ascii": "Times New Roman",
        "size": 14,
        "bold": True,
        "alignment": WD_ALIGN_PARAGRAPH.CENTER,
        "line_spacing": BODY_LINE_SPACING,
        "space_before": Pt(12),
        "space_after": Pt(6),
        "outline_level": 0,
    },
    "Heading2": {
        "font_east_asia": "黑体",
        "font_ascii": "Times New Roman",
        "size": BODY_FONT_SIZE,
        "bold": True,
        "alignment": WD_ALIGN_PARAGRAPH.LEFT,
        "line_spacing": BODY_LINE_SPACING,
        "space_before": Pt(6),
        "space_after": Pt(3),
        "outline_level": 1,
    },
    "Heading3": {
        "font_east_asia": "黑体",
        "font_ascii": "Times New Roman",
        "size": BODY_FONT_SIZE,
        "bold": True,
        "alignment": WD_ALIGN_PARAGRAPH.LEFT,
        "line_spacing": BODY_LINE_SPACING,
        "space_before": Pt(6),
        "space_after": Pt(3),
        "outline_level": 2,
    },
    "Heading4": {
        "font_east_asia": "黑体",
        "font_ascii": "Times New Roman",
        "size": BODY_FONT_SIZE,
        "bold": True,
        "alignment": WD_ALIGN_PARAGRAPH.LEFT,
        "line_spacing": BODY_LINE_SPACING,
        "space_before": Pt(6),
        "space_after": Pt(3),
        "outline_level": 3,
    },
    "BodyText": {
        "font_east_asia": "宋体",
        "font_ascii": "Times New Roman",
        "size": BODY_FONT_SIZE,
        "line_spacing": BODY_LINE_SPACING,
        "first_line_indent": BODY_FIRST_LINE_INDENT,
    },
    "ReferenceHeading": {
        "font_east_asia": "黑体",
        "font_ascii": "Times New Roman",
        "size": SMALL_SECOND_FONT_SIZE,
        "bold": True,
        "alignment": WD_ALIGN_PARAGRAPH.CENTER,
        "space_after": Pt(12),
    },
    "ReferenceEntry": {
        "font_east_asia": "宋体",
        "font_ascii": "Times New Roman",
        "size": BODY_FONT_SIZE,
        "line_spacing": BODY_LINE_SPACING,
        "first_line_indent": BODY_FIRST_LINE_INDENT,
    },
    "AppendixHeading": {
        "font_east_asia": "黑体",
        "font_ascii": "Times New Roman",
        "size": SMALL_SECOND_FONT_SIZE,
        "bold": True,
        "alignment": WD_ALIGN_PARAGRAPH.CENTER,
        "space_after": Pt(12),
    },
    "AppendixItemHeading": {
        "font_east_asia": "黑体",
        "font_ascii": "Times New Roman",
        "size": FOURTH_FONT_SIZE,
        "bold": True,
        "alignment": WD_ALIGN_PARAGRAPH.LEFT,
        "space_after": Pt(6),
    },
    "AcknowledgementHeading": {
        "font_east_asia": "黑体",
        "font_ascii": "Times New Roman",
        "size": SMALL_SECOND_FONT_SIZE,
        "bold": True,
        "alignment": WD_ALIGN_PARAGRAPH.CENTER,
        "space_after": Pt(12),
    },
    "NoteText": {
        "font_east_asia": "宋体",
        "font_ascii": "Times New Roman",
        "size": 9,
        "line_spacing": BODY_LINE_SPACING,
    },
}

HEADER_SUBTITLE_SEPARATOR_PATTERNS = (
    re.compile(r"^(?P<main>.+?)：\s*(?P<sub>.+)$"),
    re.compile(r"^(?P<main>.+?):\s+(?P<sub>.+)$"),
    re.compile(r"^(?P<main>.+?)(?:——|--)\s*(?P<sub>.+)$"),
    re.compile(r"^(?P<main>.+?)\s+-\s+(?P<sub>.+)$"),
    re.compile(r"^(?P<main>.+?)\s*\|\s*(?P<sub>.+)$"),
)
HEADER_PARENTHESES_SUBTITLE_PATTERN = re.compile(r"^(?P<main>.+?)[（(]\s*(?P<sub>[^()（）]{1,40})\s*[）)]$")


def normalize_text_block(text: str) -> str:
    return "\n".join(line.rstrip() for line in (text or "").strip().splitlines()).strip()


def primary_title_line(title: str) -> str:
    normalized = normalize_text_block(title)
    if not normalized:
        return "论文题目待补充"
    for line in normalized.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return "论文题目待补充"


def has_title_letters(text: str) -> bool:
    return bool(re.search(r"[A-Za-z\u4e00-\u9fff]", text or ""))


def looks_like_version_or_year(text: str) -> bool:
    candidate = (text or "").strip()
    return bool(re.fullmatch(r"\d{2,4}(?:[./-]\d{1,2}){0,2}(?:版)?", candidate))


def clean_header_main_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip()).rstrip("：:|-—– ")


def can_strip_subtitle(main_title: str, subtitle: str) -> bool:
    main = clean_header_main_text(main_title)
    sub = re.sub(r"\s+", " ", (subtitle or "").strip())
    if not main or not sub:
        return False
    if not has_title_letters(main) or not has_title_letters(sub):
        return False
    if len(sub) > 40:
        return False
    if re.fullmatch(r"[A-Z]{1,6}", sub):
        return False
    if looks_like_version_or_year(sub):
        return False
    return True


def strip_subtitle_for_header(title: str) -> str:
    line = primary_title_line(title)
    for pattern in HEADER_SUBTITLE_SEPARATOR_PATTERNS:
        match = pattern.match(line)
        if not match:
            continue
        main = match.group("main")
        subtitle = match.group("sub")
        if can_strip_subtitle(main, subtitle):
            return clean_header_main_text(main)

    parenthetical = HEADER_PARENTHESES_SUBTITLE_PATTERN.match(line)
    if parenthetical and can_strip_subtitle(parenthetical.group("main"), parenthetical.group("sub")):
        return clean_header_main_text(parenthetical.group("main"))
    return clean_header_main_text(line)


def extract_header_title(title: str, *, max_length: int = 60) -> str:
    clean = strip_subtitle_for_header(title) or "论文题目待补充"
    return clean[:max_length]


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


def clear_block_container(container) -> None:
    element = container._element
    for child in list(element):
        element.remove(child)


def set_rfonts(target_element, *, east_asia: str, ascii_font: str) -> None:
    rpr = target_element.get_or_add_rPr()
    rfonts = rpr.rFonts
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    rfonts.set(qn("w:ascii"), ascii_font)
    rfonts.set(qn("w:hAnsi"), ascii_font)
    rfonts.set(qn("w:cs"), ascii_font)
    rfonts.set(qn("w:eastAsia"), east_asia)


def set_style_font(style, *, east_asia: str, ascii_font: str, size: float, bold: bool = False) -> None:
    style.font.name = ascii_font
    style.font.size = Pt(size)
    style.font.bold = bold
    set_rfonts(style._element, east_asia=east_asia, ascii_font=ascii_font)


def set_run_font(run, *, east_asia: str, ascii_font: str, size: float, bold: bool = False) -> None:
    run.font.name = ascii_font
    run.font.size = Pt(size)
    run.bold = bold
    set_rfonts(run._element, east_asia=east_asia, ascii_font=ascii_font)


def get_style_by_name(document: Document, name: str):
    for style in document.styles:
        if style.name == name:
            return style
    return None


def ensure_style_name(style, name: str) -> None:
    name_element = style._element.find(qn("w:name"))
    if name_element is None:
        name_element = OxmlElement("w:name")
        style._element.insert(0, name_element)
    name_element.set(qn("w:val"), name)


def set_style_outline_level(style, level: int) -> None:
    ppr = style._element.get_or_add_pPr()
    for node in list(ppr):
        if node.tag == qn("w:outlineLvl"):
            ppr.remove(node)
    outline = OxmlElement("w:outlineLvl")
    outline.set(qn("w:val"), str(level))
    ppr.append(outline)


def ensure_paragraph_style(document: Document, name: str, *, base: str = "Normal", **spec) -> None:
    styles = document.styles
    style = get_style_by_name(document, name)
    if style is None:
        style = styles.add_style(STYLE_IDS[name], WD_STYLE_TYPE.PARAGRAPH)
        ensure_style_name(style, name)

    if base == "Normal":
        style.base_style = styles["Normal"]
    else:
        base_style = get_style_by_name(document, base)
        if base_style is not None:
            style.base_style = base_style

    set_style_font(
        style,
        east_asia=spec.get("font_east_asia", STYLE_BASE_FONTS["cn_body"]),
        ascii_font=spec.get("font_ascii", STYLE_BASE_FONTS["latin"]),
        size=spec.get("size", BODY_FONT_SIZE),
        bold=spec.get("bold", False),
    )

    paragraph_format = style.paragraph_format
    paragraph_format.alignment = spec.get("alignment")
    paragraph_format.first_line_indent = spec.get("first_line_indent")
    paragraph_format.left_indent = spec.get("left_indent")
    paragraph_format.space_before = spec.get("space_before", Pt(0))
    paragraph_format.space_after = spec.get("space_after", Pt(0))
    paragraph_format.line_spacing = spec.get("line_spacing", BODY_LINE_SPACING)
    paragraph_format.keep_with_next = spec.get("keep_with_next", False)

    if "outline_level" in spec:
        set_style_outline_level(style, spec["outline_level"])


def ensure_styles(document: Document) -> None:
    normal = document.styles["Normal"]
    set_style_font(normal, east_asia="宋体", ascii_font="Times New Roman", size=BODY_FONT_SIZE)
    normal_format = normal.paragraph_format
    normal_format.line_spacing = BODY_LINE_SPACING
    normal_format.first_line_indent = BODY_FIRST_LINE_INDENT
    normal_format.space_after = Pt(0)
    normal_format.space_before = Pt(0)

    for style_name, spec in STYLE_SPECS.items():
        ensure_paragraph_style(document, style_name, **spec)


def configure_section_layout(section) -> None:
    section.orientation = WD_ORIENT.PORTRAIT
    section.page_width = Cm(A4_WIDTH_CM)
    section.page_height = Cm(A4_HEIGHT_CM)
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin = Cm(2)
    section.right_margin = Cm(2)
    section.gutter = Cm(0.5)
    section.header_distance = Cm(1.5)
    section.footer_distance = Cm(1.5)


def set_update_fields_on_open(document: Document) -> None:
    settings = document.settings._element
    node = settings.find(qn("w:updateFields"))
    if node is None:
        node = OxmlElement("w:updateFields")
        settings.append(node)
    node.set(qn("w:val"), "true")


def add_field(run, instruction: str, placeholder: str | None = None) -> None:
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr_text = OxmlElement("w:instrText")
    instr_text.set(qn("xml:space"), "preserve")
    instr_text.text = instruction
    fld_separate = OxmlElement("w:fldChar")
    fld_separate.set(qn("w:fldCharType"), "separate")
    run._r.extend([fld_begin, instr_text, fld_separate])
    if placeholder:
        text = OxmlElement("w:t")
        text.text = placeholder
        run._r.append(text)
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_end)


def configure_header_footer(document: Document, title: str) -> None:
    for section in document.sections:
        section.header.is_linked_to_previous = False
        section.footer.is_linked_to_previous = False

        clear_block_container(section.header)
        header_paragraph = section.header.add_paragraph()
        header_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        header_run = header_paragraph.add_run(extract_header_title(title))
        set_run_font(header_run, east_asia="宋体", ascii_font="Times New Roman", size=FIFTH_FONT_SIZE)

        clear_block_container(section.footer)
        footer_paragraph = section.footer.add_paragraph()
        footer_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        footer_run = footer_paragraph.add_run()
        set_run_font(footer_run, east_asia="黑体", ascii_font="Times New Roman", size=FIFTH_FONT_SIZE, bold=True)
        add_field(footer_run, "PAGE")


def configure_document(document: Document, title: str) -> None:
    clear_document(document)
    ensure_styles(document)
    set_update_fields_on_open(document)
    for section in document.sections:
        configure_section_layout(section)
    configure_header_footer(document, title)


def add_page_break(document: Document) -> None:
    document.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def add_heading_paragraph(document: Document, text: str, style_name: str) -> None:
    paragraph = document.add_paragraph(style=get_style_by_name(document, style_name))
    paragraph.add_run(text)


def add_body_paragraphs(document: Document, text: str, *, style_name: str) -> None:
    normalized = normalize_text_block(text)
    if not normalized:
        return
    blocks = [item.strip() for item in re.split(r"\n\s*\n", normalized) if item.strip()]
    for block in blocks:
        paragraph = document.add_paragraph(style=get_style_by_name(document, style_name))
        paragraph.add_run(block)


def add_keywords(document: Document, keywords: list[str], *, english: bool) -> None:
    if not keywords:
        return
    paragraph = document.add_paragraph(style=get_style_by_name(document, "KeywordsLabel"))
    label = "Keywords" if english else "关键词"
    separator = ", " if english else "，"
    label_run = paragraph.add_run(f"{label}: ")
    if english:
        set_run_font(label_run, east_asia="Times New Roman", ascii_font="Times New Roman", size=BODY_FONT_SIZE, bold=True)
    else:
        set_run_font(label_run, east_asia="宋体", ascii_font="Times New Roman", size=BODY_FONT_SIZE, bold=True)

    content_run = paragraph.add_run(separator.join(item.strip() for item in keywords if item.strip()))
    if english:
        set_run_font(content_run, east_asia="Times New Roman", ascii_font="Times New Roman", size=BODY_FONT_SIZE)
    else:
        set_run_font(content_run, east_asia="宋体", ascii_font="Times New Roman", size=BODY_FONT_SIZE)


def add_abstract_page(document: Document, thesis: NormalizedThesis, *, english: bool) -> None:
    if english:
        add_heading_paragraph(document, "Abstract", "EnglishAbstractHeading")
        add_body_paragraphs(document, thesis.abstract_en.content, style_name="EnglishAbstractBody")
        add_keywords(document, thesis.abstract_en.keywords, english=True)
        return

    title = thesis.metadata.title.strip() or "论文题目待补充"
    add_heading_paragraph(document, title, "ThesisTitle")
    add_heading_paragraph(document, "中文摘要", "ChineseAbstractHeading")
    add_body_paragraphs(document, thesis.abstract_cn.content, style_name="ChineseAbstractBody")
    add_keywords(document, thesis.abstract_cn.keywords, english=False)


def add_toc(document: Document) -> None:
    add_heading_paragraph(document, "目录", "TOCHeading")
    paragraph = document.add_paragraph(style=get_style_by_name(document, "BodyText"))
    run = paragraph.add_run()
    add_field(run, 'TOC \\o "1-4" \\h \\z \\u', placeholder="请在 Word 中更新目录字段。")


def section_number(section: BodySection, counters: list[int]) -> str:
    level = min(max(section.level, 1), 4)
    for index in range(level - 1):
        if counters[index] == 0:
            counters[index] = 1
    counters[level - 1] += 1
    for index in range(level, 4):
        counters[index] = 0
    return ".".join(str(counters[index]) for index in range(level)) + "."


def add_body(document: Document, body_sections: list[BodySection]) -> None:
    counters = [0, 0, 0, 0]
    for section in body_sections:
        level = min(max(section.level, 1), 4)
        prefix = section_number(section, counters)
        heading_text = f"{prefix} {section.title.strip() or '正文'}"
        add_heading_paragraph(document, heading_text, f"Heading{level}")
        add_body_paragraphs(document, section.content, style_name="BodyText")


def add_notes(document: Document, text: str) -> None:
    normalized = normalize_text_block(text)
    if not normalized:
        return
    add_heading_paragraph(document, "注释", "ReferenceHeading")
    add_body_paragraphs(document, normalized, style_name="NoteText")


def add_references(document: Document, items: list[str]) -> None:
    add_heading_paragraph(document, "参考文献", "ReferenceHeading")
    for item in [entry.strip() for entry in items if entry.strip()]:
        paragraph = document.add_paragraph(style=get_style_by_name(document, "ReferenceEntry"))
        paragraph.add_run(item)


def looks_like_appendix_item_heading(line: str) -> bool:
    text = line.strip()
    if not text or len(text) > 40:
        return False
    return bool(re.match(r"^(附录\s*[A-Z0-9一二三四五六七八九十]+|[A-Z0-9一二三四五六七八九十]+[、.]\s*.+)$", text))


def add_appendix(document: Document, text: str) -> None:
    normalized = normalize_text_block(text)
    if not normalized:
        return
    add_heading_paragraph(document, "附录", "AppendixHeading")
    blocks = [item.strip() for item in re.split(r"\n\s*\n", normalized) if item.strip()]
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        if looks_like_appendix_item_heading(lines[0]):
            heading = document.add_paragraph(style=get_style_by_name(document, "AppendixItemHeading"))
            heading.add_run(lines[0])
            remainder = "\n".join(lines[1:]).strip()
            if remainder:
                add_body_paragraphs(document, remainder, style_name="BodyText")
            continue
        add_body_paragraphs(document, block, style_name="BodyText")


def add_acknowledgements(document: Document, text: str) -> None:
    normalized = normalize_text_block(text)
    if not normalized:
        return
    add_heading_paragraph(document, "致谢", "AcknowledgementHeading")
    add_body_paragraphs(document, normalized, style_name="BodyText")


def load_template_document() -> Document:
    if not TEMPLATE_DOCX_PATH.exists():
        raise AppError(
            "TEMPLATE_DEPENDENCY_MISSING",
            "Word 模板不存在，无法生成导出结果。",
            details={"template": str(TEMPLATE_DOCX_PATH)},
            status_code=500,
        )
    try:
        return Document(TEMPLATE_DOCX_PATH)
    except Exception as exc:  # pragma: no cover
        raise AppError(
            "TEMPLATE_DEPENDENCY_MISSING",
            "Word 模板无法加载，请检查模板文件是否损坏。",
            details={"template": str(TEMPLATE_DOCX_PATH), "reason": str(exc)},
            status_code=500,
        ) from exc


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
        configure_document(document, thesis.metadata.title.strip())

        add_abstract_page(document, thesis, english=False)
        add_page_break(document)
        add_abstract_page(document, thesis, english=True)
        add_page_break(document)
        add_toc(document)
        add_page_break(document)
        add_body(document, thesis.body_sections)

        if normalize_text_block(thesis.notes):
            add_page_break(document)
            add_notes(document, thesis.notes)

        add_page_break(document)
        add_references(document, thesis.references.items)

        if normalize_text_block(thesis.appendix):
            add_page_break(document)
            add_appendix(document, thesis.appendix)

        if normalize_text_block(thesis.acknowledgements):
            add_page_break(document)
            add_acknowledgements(document, thesis.acknowledgements)

        buffer = io.BytesIO()
        document.save(buffer)
        payload = buffer.getvalue()
        persist_debug_copy("export-docx", payload, "docx")
        return payload
    except AppError:
        raise
    except Exception as exc:  # pragma: no cover
        raise AppError(
            "EXPORT_FAILED",
            "Word 文件生成失败，请稍后重试。",
            details={"reason": str(exc)},
            status_code=500,
        ) from exc
