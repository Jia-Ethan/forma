from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from docx import Document

from ..contracts import BodySection, CapabilityFlags, MetadataFields, NormalizedThesis, ReferenceSection, SummarySection
from ..errors import AppError

SPECIAL_TITLE_MAP = {
    "摘要": "abstract_cn",
    "中文摘要": "abstract_cn",
    "abstract": "abstract_en",
    "参考文献": "references",
    "references": "references",
    "致谢": "acknowledgements",
    "致謝": "acknowledgements",
    "acknowledgements": "acknowledgements",
    "acknowledgment": "acknowledgements",
    "appendix": "appendix",
    "附录": "appendix",
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


def detect_heading(paragraph_text: str, style_name: Optional[str]) -> Tuple[bool, str, int]:
    text = paragraph_text.strip()
    style = (style_name or "").strip().lower()
    if style.startswith("heading"):
        level_text = re.sub(r"\D+", "", style)
        level = int(level_text) if level_text else 1
        return True, text, min(level, 3)

    markdown_match = re.match(r"^(#{1,3})\s+(.+)$", text)
    if markdown_match:
        hashes, title = markdown_match.groups()
        return True, title.strip(), len(hashes)

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
    prefixes = ["keywords", "keyword"] if english else ["关键词", "關鍵詞"]
    for line in lines:
        normalized = line.lower().replace("：", ":")
        matched = False
        for prefix in prefixes:
            if normalized.startswith(prefix):
                keywords = line.split(":", 1)[-1].split("：", 1)[-1].strip()
                matched = True
                break
        if not matched:
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

    thesis = normalized_from_paragraphs(paragraphs, "docx", capabilities)
    if not thesis.warnings and len(document.paragraphs) <= 2:
        thesis.warnings.append("文档段落较少，请检查是否上传了完整论文内容。")
    return thesis


def normalize_text_input(text: str, capabilities: CapabilityFlags) -> NormalizedThesis:
    paragraphs = [(line, None) for line in text.splitlines()]
    return normalized_from_paragraphs(paragraphs, "text", capabilities)


def normalized_from_paragraphs(
    paragraphs: List[Tuple[str, Optional[str]]],
    source_type: str,
    capabilities: CapabilityFlags,
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

        is_heading, heading_title, level = detect_heading(value, style_name)
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
    references: list[str] = []
    acknowledgements = ""
    appendix = ""

    for index, section in enumerate(sections, start=1):
        if section.kind == "abstract_cn" and not abstract_cn:
            abstract_cn, abstract_cn_keywords = split_keywords(section.content, english=False)
        elif section.kind == "abstract_en" and not abstract_en:
            abstract_en, abstract_en_keywords = split_keywords(section.content, english=True)
        elif section.kind == "references":
            references = [item.strip() for item in section.content.splitlines() if item.strip()]
        elif section.kind == "acknowledgements":
            acknowledgements = section.content.strip()
        elif section.kind == "appendix":
            appendix = section.content.strip()
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
        warnings.append("未识别到 Abstract，可在下一步补充。")
    if not body_sections:
        raise AppError("CONTENT_EMPTY", "未识别到可用正文内容", status_code=400)

    return NormalizedThesis(
        source_type="docx" if source_type == "docx" else "text",
        metadata=MetadataFields(title=title),
        abstract_cn=SummarySection(content=abstract_cn, keywords=abstract_cn_keywords),
        abstract_en=SummarySection(content=abstract_en, keywords=abstract_en_keywords),
        body_sections=body_sections,
        references=ReferenceSection(items=references),
        acknowledgements=acknowledgements,
        appendix=appendix,
        warnings=warnings,
        parse_errors=[],
        capabilities=build_capabilities(capabilities),
    )
