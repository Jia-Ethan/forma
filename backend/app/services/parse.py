from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple
from xml.etree import ElementTree as ET

from docx import Document

from ..contracts import BodySection, CapabilityFlags, MetadataFields, NormalizedThesis, ReferenceSection, SummarySection
from ..errors import AppError

SPECIAL_TITLE_MAP = {
    "摘要": "abstract_cn",
    "中文摘要": "abstract_cn",
    "abstract": "abstract_en",
    "外文摘要": "abstract_en",
    "参考文献": "references",
    "references": "references",
    "致谢": "acknowledgements",
    "致謝": "acknowledgements",
    "acknowledgements": "acknowledgements",
    "acknowledgment": "acknowledgements",
    "appendix": "appendix",
    "附录": "appendix",
    "目录": "toc",
    "contents": "toc",
    "注释": "notes",
    "注解": "notes",
    "notes": "notes",
}

WORD_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
NUMBERED_HEADING_RE = re.compile(r"^(?P<index>\d+(?:\.\d+){0,3})[\.．]?\s+(?P<title>.+)$")
REFERENCE_ENTRY_MARKER_RE = re.compile(r"\[[A-Z]{1,3}\]", flags=re.IGNORECASE)
ENGLISH_KEYWORD_PREFIX_RE = re.compile(r"^(keyword|keywords|key words)\s*:", flags=re.IGNORECASE)
CHINESE_KEYWORD_PREFIX_RE = re.compile(r"^(关键词|關鍵詞)\s*:")
NUMBERED_HEADING_BLOCKED_KINDS = {"references", "notes", "appendix", "toc"}
COMPLEX_FEATURE_WARNINGS = {
    "tables": "检测到表格内容，当前导出为重新排版模式，表格需人工复核。",
    "images": "检测到图片内容，当前导出不保证图题与版式位置完全保真。",
    "footnotes": "检测到脚注内容，当前不自动保证页末注格式完全合规。",
    "endnotes": "检测到篇末注内容，当前不自动保证注释编号与版式完全合规。",
}


@dataclass
class SectionDraft:
    kind: str
    title: str
    level: int
    content: str


def normalize_title(value: str) -> str:
    text = value.strip().strip("#").strip()
    return re.sub(r"[\s:：\-\._]+", "", text).lower()


def looks_like_reference_entry(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    if REFERENCE_ENTRY_MARKER_RE.search(stripped):
        return True
    if re.search(r"\b(?:doi|vol\.|no\.|pp\.)\b", stripped, flags=re.IGNORECASE):
        return True
    if re.search(r"(出版社|期刊|学报|學報|论文集|論文集)", stripped):
        return True
    return bool(re.search(r"\b(?:19|20)\d{2}\b", stripped) and re.search(r"[，,.:：]", stripped))


def looks_like_numbered_list_item(title: str) -> bool:
    text = title.strip()
    if not text:
        return True
    if len(text) > 60:
        return True
    if re.search(r"[.．。！？!?；;]$", text):
        return True
    if len(re.findall(r"[，,；;。！？!?]", text)) >= 2:
        return True
    if REFERENCE_ENTRY_MARKER_RE.search(text):
        return True
    return bool(re.search(r"\b(?:19|20)\d{2}\b", text) and re.search(r"[，,.:：]", text))


def detect_heading(paragraph_text: str, style_name: Optional[str], current_kind: str = "body") -> Tuple[bool, str, int]:
    text = paragraph_text.strip()
    style = (style_name or "").strip().lower().replace(" ", "")
    if style.startswith("heading"):
        level_text = re.sub(r"\D+", "", style)
        level = int(level_text) if level_text else 1
        return True, text, min(level, 4)

    markdown_match = re.match(r"^(#{1,4})\s+(.+)$", text)
    if markdown_match:
        hashes, title = markdown_match.groups()
        return True, title.strip(), len(hashes)

    numbered_match = NUMBERED_HEADING_RE.match(text)
    if numbered_match and current_kind not in NUMBERED_HEADING_BLOCKED_KINDS:
        index = numbered_match.group("index")
        title = numbered_match.group("title").strip()
        if title and not looks_like_reference_entry(text) and not looks_like_numbered_list_item(title):
            return True, title, min(index.count(".") + 1, 4)

    normalized = normalize_title(text)
    if normalized in SPECIAL_TITLE_MAP:
        return True, text, 1

    if re.match(r"^第[一二三四五六七八九十百0-9]+章", text):
        return True, text, 1

    return False, "", 0


def split_keywords(text: str, english: bool) -> tuple[str, list[str]]:
    lines = [line.strip() for line in text.splitlines()]
    body_lines: list[str] = []
    keywords = ""
    prefix_pattern = ENGLISH_KEYWORD_PREFIX_RE if english else CHINESE_KEYWORD_PREFIX_RE
    for line in lines:
        normalized = line.strip().replace("：", ":")
        if prefix_pattern.match(normalized):
            keywords = normalized.split(":", 1)[-1].strip()
        else:
            body_lines.append(line)
    items = [item.strip() for item in re.split(r"[，,；;、]", keywords) if item.strip()]
    return "\n".join(body_lines).strip(), items


def build_capabilities(capabilities: CapabilityFlags) -> CapabilityFlags:
    return capabilities.model_copy(deep=True)


def normalize_body_text(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def looks_like_title(value: str) -> bool:
    text = value.strip()
    if not text:
        return False
    if len(text) > 40:
        return False
    normalized = normalize_title(text)
    if normalized in SPECIAL_TITLE_MAP or normalized in {"正文", "无标题", "引言", "绪论", "前言", "结论"}:
        return False
    if re.match(r"^(第[一二三四五六七八九十百0-9]+章|chapter\s+\d+)", text, flags=re.IGNORECASE):
        return False
    return True


def extract_title(front_matter: list[str], sections: list[SectionDraft]) -> str:
    for candidate in front_matter[:3]:
        if looks_like_title(candidate):
            return candidate.strip()

    for section in sections:
        if section.kind == "body" and looks_like_title(section.title):
            body_text = normalize_body_text(section.content)
            if len(body_text) > 120:
                return section.title.strip()

    return ""


def note_part_has_user_content(data: bytes, tag_name: str) -> bool:
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        return False
    for node in root.findall(f"w:{tag_name}", WORD_NS):
        note_id = node.attrib.get(f"{{{WORD_NS['w']}}}id")
        if note_id in {"-1", "0", "1"}:
            continue
        text = "".join(node.itertext()).strip()
        if text:
            return True
    return False


def inspect_docx_features(path: Path, document: Document) -> list[str]:
    features: list[str] = []
    if document.tables:
        features.append("tables")

    try:
        with zipfile.ZipFile(path) as archive:
            names = set(archive.namelist())
            if any(name.startswith("word/media/") for name in names):
                features.append("images")
            if "word/footnotes.xml" in names and note_part_has_user_content(archive.read("word/footnotes.xml"), "footnote"):
                features.append("footnotes")
            if "word/endnotes.xml" in names and note_part_has_user_content(archive.read("word/endnotes.xml"), "endnote"):
                features.append("endnotes")
    except zipfile.BadZipFile:
        raise AppError("DOCX_INVALID", "上传文件不是有效的 .docx 文档，请确认文件未损坏。", status_code=400) from None

    seen: set[str] = set()
    ordered: list[str] = []
    for item in features:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def parse_docx_file(path: Path, capabilities: CapabilityFlags) -> NormalizedThesis:
    if path.suffix.lower() != ".docx":
        raise AppError("UNSUPPORTED_FILE_TYPE", "仅支持上传 .docx 文件", status_code=400)

    try:
        document = Document(path)
    except Exception as exc:  # pragma: no cover
        raise AppError("PARSE_FAILED", "无法读取这个 .docx 的正文内容，请确认文件未损坏。", details={"reason": str(exc)}, status_code=400) from exc

    paragraphs: List[Tuple[str, Optional[str]]] = []
    for paragraph in document.paragraphs:
        style_name = paragraph.style.name if paragraph.style is not None else None
        paragraphs.append((paragraph.text, style_name))

    source_features = inspect_docx_features(path, document)
    thesis = normalized_from_paragraphs(paragraphs, "docx", capabilities, source_features=source_features)
    for feature in source_features:
        warning = COMPLEX_FEATURE_WARNINGS.get(feature)
        if warning and warning not in thesis.warnings:
            thesis.warnings.append(warning)
    if not thesis.warnings and len(document.paragraphs) <= 2:
        thesis.warnings.append("文档段落较少，请检查是否上传了完整论文内容。")
    return thesis


def normalize_text_input(text: str, capabilities: CapabilityFlags) -> NormalizedThesis:
    paragraphs = [(line, None) for line in text.splitlines()]
    return normalized_from_paragraphs(paragraphs, "text", capabilities, source_features=[])


def normalized_from_paragraphs(
    paragraphs: List[Tuple[str, Optional[str]]],
    source_type: str,
    capabilities: CapabilityFlags,
    *,
    source_features: list[str],
) -> NormalizedThesis:
    sections: list[SectionDraft] = []
    warnings: list[str] = []
    current_title = ""
    current_kind = "body"
    current_level = 1
    current_lines: list[str] = []
    front_matter: list[str] = []

    def flush_current() -> None:
        nonlocal current_title, current_kind, current_level, current_lines
        content = "\n".join(line for line in current_lines if line.strip()).strip()
        if current_title or content:
            sections.append(
                SectionDraft(
                    kind=current_kind,
                    title=current_title or "正文",
                    level=current_level or 1,
                    content=content,
                )
            )
        current_title = ""
        current_kind = "body"
        current_level = 1
        current_lines = []

    for text, style_name in paragraphs:
        value = text.strip()
        if not value:
            if current_lines:
                current_lines.append("")
            continue

        is_heading, heading_title, level = detect_heading(value, style_name, current_kind)
        if is_heading:
            flush_current()
            current_title = heading_title
            current_kind = SPECIAL_TITLE_MAP.get(normalize_title(heading_title), "body")
            current_level = level or 1
            continue

        if current_title:
            current_lines.append(value)
        else:
            front_matter.append(value)

    flush_current()

    if not sections and front_matter:
        sections.append(SectionDraft(kind="body", title="正文", level=1, content="\n".join(front_matter).strip()))
    elif front_matter:
        warnings.append("检测到未归类的前置内容，已并入正文开头。")
        for section in sections:
            if section.kind == "body":
                section.content = "\n".join(front_matter + [section.content]).strip()
                break
        else:
            sections.insert(0, SectionDraft(kind="body", title="正文", level=1, content="\n".join(front_matter).strip()))

    if not sections:
        raise AppError("CONTENT_EMPTY", "文档中没有可用文本内容", status_code=400)

    title = extract_title(front_matter, sections)
    body_sections: list[BodySection] = []
    abstract_cn = ""
    abstract_cn_keywords: list[str] = []
    abstract_en = ""
    abstract_en_keywords: list[str] = []
    notes = ""
    references: list[str] = []
    acknowledgements = ""
    appendix = ""

    for index, section in enumerate(sections, start=1):
        if section.kind == "abstract_cn" and not abstract_cn:
            abstract_cn, abstract_cn_keywords = split_keywords(section.content, english=False)
        elif section.kind == "abstract_en" and not abstract_en:
            abstract_en, abstract_en_keywords = split_keywords(section.content, english=True)
        elif section.kind == "notes":
            notes = "\n\n".join(part for part in [notes, section.content.strip()] if part)
        elif section.kind == "references":
            references = [item.strip() for item in section.content.splitlines() if item.strip()]
        elif section.kind == "acknowledgements":
            acknowledgements = section.content.strip()
        elif section.kind == "appendix":
            appendix = section.content.strip()
        elif section.kind == "toc":
            continue
        else:
            body_sections.append(
                BodySection(
                    id=f"section-{index}",
                    level=section.level,
                    title=section.title.strip() or "正文",
                    content=section.content.strip(),
                )
            )

    if not abstract_cn:
        warnings.append("未识别到中文摘要，可在下一步补充。")
    if not abstract_en:
        warnings.append("未识别到外文摘要，可在下一步补充。")
    if not body_sections:
        raise AppError("CONTENT_EMPTY", "未识别到可用正文内容", status_code=400)

    return NormalizedThesis(
        source_type="docx" if source_type == "docx" else "text",
        metadata=MetadataFields(title=title),
        abstract_cn=SummarySection(content=abstract_cn, keywords=abstract_cn_keywords),
        abstract_en=SummarySection(content=abstract_en, keywords=abstract_en_keywords),
        body_sections=body_sections,
        notes=notes,
        references=ReferenceSection(items=references),
        acknowledgements=acknowledgements,
        appendix=appendix,
        source_features=source_features,
        warnings=warnings,
        parse_errors=[],
        capabilities=build_capabilities(capabilities),
    )
