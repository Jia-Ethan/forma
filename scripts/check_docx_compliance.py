from __future__ import annotations

import argparse
import json
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from docx import Document
from docx.oxml.ns import qn

from backend.app.services.export import extract_header_title

WORD_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
EXPECTED_STYLES = [
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
]


@dataclass
class CheckResult:
    id: str
    status: str
    message: str
    details: dict[str, Any]


@dataclass
class ComplianceReport:
    path: str
    results: list[CheckResult]

    @property
    def summary(self) -> dict[str, int]:
        counts = {"PASS": 0, "MANUAL_REVIEW": 0, "NOT_SUPPORTED": 0}
        for result in self.results:
            counts[result.status] = counts.get(result.status, 0) + 1
        return counts

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "summary": self.summary,
            "results": [asdict(item) for item in self.results],
        }


def approx(value: float, expected: float, tolerance: float = 0.08) -> bool:
    return abs(value - expected) <= tolerance


def get_style_by_name(document: Document, name: str):
    for style in document.styles:
        if style.name == name:
            return style
    return None


def extract_rfonts_from_style(style) -> dict[str, Any]:
    rpr = style._element.get_or_add_rPr()
    rfonts = rpr.rFonts
    size = style.font.size.pt if style.font.size is not None else None
    bold = bool(style.font.bold)
    if rfonts is None:
        return {"ascii": None, "hAnsi": None, "eastAsia": None, "size": size, "bold": bold}
    return {
        "ascii": rfonts.get(qn("w:ascii")),
        "hAnsi": rfonts.get(qn("w:hAnsi")),
        "eastAsia": rfonts.get(qn("w:eastAsia")),
        "size": size,
        "bold": bold,
    }


def extract_first_run_props(xml_bytes: bytes) -> dict[str, Any]:
    root = ET.fromstring(xml_bytes)
    run = root.find(".//w:r", WORD_NS)
    if run is None:
        return {}
    rpr = run.find("w:rPr", WORD_NS)
    if rpr is None:
        return {}
    rfonts = rpr.find("w:rFonts", WORD_NS)
    size = rpr.find("w:sz", WORD_NS)
    return {
        "ascii": rfonts.attrib.get(f"{{{WORD_NS['w']}}}ascii") if rfonts is not None else None,
        "hAnsi": rfonts.attrib.get(f"{{{WORD_NS['w']}}}hAnsi") if rfonts is not None else None,
        "eastAsia": rfonts.attrib.get(f"{{{WORD_NS['w']}}}eastAsia") if rfonts is not None else None,
        "size": (int(size.attrib.get(f"{{{WORD_NS['w']}}}val")) / 2) if size is not None else None,
        "bold": (lambda node: node is not None and node.attrib.get(f"{{{WORD_NS['w']}}}val", "1") not in {"0", "false", "False"})(rpr.find("w:b", WORD_NS)),
    }


def nonempty_paragraphs(document: Document) -> list[tuple[int, str, str]]:
    return [(index, paragraph.style.name, paragraph.text.strip()) for index, paragraph in enumerate(document.paragraphs) if paragraph.text.strip()]


def find_index(paragraphs: list[tuple[int, str, str]], *, text: str | None = None, style: str | None = None):
    for index, style_name, paragraph_text in paragraphs:
        if text is not None and paragraph_text != text:
            continue
        if style is not None and style_name != style:
            continue
        return index
    return None


def make_result(results: list[CheckResult], id: str, status: str, message: str, **details: Any) -> None:
    results.append(CheckResult(id=id, status=status, message=message, details=details))


def check_docx(path: Path) -> ComplianceReport:
    document = Document(path)
    results: list[CheckResult] = []
    paragraphs = nonempty_paragraphs(document)

    sections = list(document.sections)
    if not sections:
        make_result(results, "page_setup", "MANUAL_REVIEW", "文档未包含 section 信息。", sections=0)
    else:
        section = sections[0]
        size_ok = approx(section.page_width.cm, 21) and approx(section.page_height.cm, 29.7)
        make_result(
            results,
            "page_size",
            "PASS" if size_ok else "MANUAL_REVIEW",
            "页面尺寸已检查。" if size_ok else "页面尺寸与 A4 不一致。",
            page_width_cm=round(section.page_width.cm, 3),
            page_height_cm=round(section.page_height.cm, 3),
        )
        margins_ok = all(
            [
                approx(section.top_margin.cm, 2.5),
                approx(section.bottom_margin.cm, 2.5),
                approx(section.left_margin.cm, 2),
                approx(section.right_margin.cm, 2),
                approx(section.gutter.cm, 0.5),
            ]
        )
        make_result(
            results,
            "margins_gutter",
            "PASS" if margins_ok else "MANUAL_REVIEW",
            "页边距与装订线已符合预期。" if margins_ok else "页边距或装订线与规范不一致。",
            top_cm=round(section.top_margin.cm, 3),
            bottom_cm=round(section.bottom_margin.cm, 3),
            left_cm=round(section.left_margin.cm, 3),
            right_cm=round(section.right_margin.cm, 3),
            gutter_cm=round(section.gutter.cm, 3),
        )

    missing_styles = [name for name in EXPECTED_STYLES if get_style_by_name(document, name) is None]
    make_result(
        results,
        "style_catalog",
        "PASS" if not missing_styles else "MANUAL_REVIEW",
        "关键样式均存在。" if not missing_styles else "缺少部分关键样式。",
        missing_styles=missing_styles,
    )

    body_style = get_style_by_name(document, "BodyText")
    if body_style is None:
        make_result(results, "body_style", "MANUAL_REVIEW", "未找到 BodyText 样式。", expected="宋体 / Times New Roman / 小四 / 1.25 倍行距")
    else:
        body_font = extract_rfonts_from_style(body_style)
        body_ok = (
            body_font["eastAsia"] == "宋体"
            and body_font["ascii"] == "Times New Roman"
            and approx(body_font["size"] or 0, 12, 0.2)
            and approx(float(body_style.paragraph_format.line_spacing or 0), 1.25, 0.01)
        )
        make_result(results, "body_style", "PASS" if body_ok else "MANUAL_REVIEW", "正文样式已检查。" if body_ok else "正文样式与规范不一致。", **body_font, line_spacing=body_style.paragraph_format.line_spacing)

    cn_style = get_style_by_name(document, "ChineseAbstractHeading")
    cn_body_style = get_style_by_name(document, "ChineseAbstractBody")
    cn_ok = False
    if cn_style is not None and cn_body_style is not None:
        heading_font = extract_rfonts_from_style(cn_style)
        body_font = extract_rfonts_from_style(cn_body_style)
        cn_ok = heading_font["eastAsia"] == "黑体" and approx(heading_font["size"] or 0, 18, 0.2) and body_font["eastAsia"] == "宋体"
        make_result(results, "cn_abstract_style", "PASS" if cn_ok else "MANUAL_REVIEW", "中文摘要样式已检查。" if cn_ok else "中文摘要标题或正文样式不符合预期。", heading=heading_font, body=body_font)
    else:
        make_result(results, "cn_abstract_style", "MANUAL_REVIEW", "中文摘要样式缺失。", missing=[name for name in ["ChineseAbstractHeading", "ChineseAbstractBody"] if get_style_by_name(document, name) is None])

    en_style = get_style_by_name(document, "EnglishAbstractBody")
    if en_style is None:
        make_result(results, "en_abstract_style", "MANUAL_REVIEW", "未找到 EnglishAbstractBody 样式。", expected="Times New Roman / 小四")
    else:
        en_font = extract_rfonts_from_style(en_style)
        en_ok = en_font["eastAsia"] == "Times New Roman" and en_font["ascii"] == "Times New Roman" and approx(en_font["size"] or 0, 12, 0.2)
        make_result(results, "en_abstract_style", "PASS" if en_ok else "MANUAL_REVIEW", "英文摘要样式已检查。" if en_ok else "英文摘要字体或字号不符合预期。", **en_font)

    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        document_xml = archive.read("word/document.xml").decode("utf-8")
        toc_ok = 'TOC \\o "1-4" \\h \\z \\u' in document_xml
        make_result(results, "toc_field", "PASS" if toc_ok else "MANUAL_REVIEW", "目录字段已存在。" if toc_ok else "未检测到目录字段。")

        header_files = sorted(name for name in names if name.startswith("word/header"))
        footer_files = sorted(name for name in names if name.startswith("word/footer"))
        thesis_title = next((text for _, style, text in paragraphs if style == "ThesisTitle"), "")

        if header_files:
            header_xml = archive.read(header_files[0])
            header_root = ET.fromstring(header_xml)
            header_text = "".join(header_root.itertext()).strip()
            expected_header_title = extract_header_title(thesis_title) if thesis_title else ""
            header_ok = bool(header_text) and bool(expected_header_title) and header_text == expected_header_title
            make_result(
                results,
                "header_title",
                "PASS" if header_ok else "MANUAL_REVIEW",
                "页眉内容已检查。" if header_ok else "页眉未正确写入论文主标题。",
                header_text=header_text,
                thesis_title=thesis_title,
                expected_header_title=expected_header_title,
            )
            header_props = extract_first_run_props(header_xml)
            header_font_ok = header_props.get("eastAsia") == "宋体" and approx(float(header_props.get("size") or 0), 10.5, 0.2)
            make_result(results, "header_font", "PASS" if header_font_ok else "MANUAL_REVIEW", "页眉字体已检查。" if header_font_ok else "页眉字体或字号不符合预期。", **header_props)
        else:
            make_result(results, "header_title", "MANUAL_REVIEW", "未检测到页眉部件。")
            make_result(results, "header_font", "MANUAL_REVIEW", "无法检查页眉字体。")

        if footer_files:
            footer_xml = archive.read(footer_files[0])
            footer_text = footer_xml.decode("utf-8")
            page_ok = "PAGE" in footer_text
            make_result(results, "footer_page_field", "PASS" if page_ok else "MANUAL_REVIEW", "页脚页码字段已存在。" if page_ok else "未检测到页码字段。")
            footer_props = extract_first_run_props(footer_xml)
            footer_font_ok = footer_props.get("eastAsia") == "黑体" and approx(float(footer_props.get("size") or 0), 10.5, 0.2) and bool(footer_props.get("bold"))
            make_result(results, "footer_font", "PASS" if footer_font_ok else "MANUAL_REVIEW", "页脚样式已检查。" if footer_font_ok else "页脚字体、字号或加粗不符合预期。", **footer_props)
        else:
            make_result(results, "footer_page_field", "MANUAL_REVIEW", "未检测到页脚部件。")
            make_result(results, "footer_font", "MANUAL_REVIEW", "无法检查页脚字体。")

    cn_index = find_index(paragraphs, text="中文摘要")
    en_index = find_index(paragraphs, text="Abstract")
    toc_index = find_index(paragraphs, text="目录")
    body_index = find_index(paragraphs, style="Heading1")
    ref_index = find_index(paragraphs, text="参考文献")
    appendix_index = find_index(paragraphs, text="附录")
    ack_index = find_index(paragraphs, text="致谢")

    order_ok = all(index is not None for index in [cn_index, en_index, toc_index, body_index, ref_index])
    if order_ok:
        order_ok = cn_index < en_index < toc_index < body_index < ref_index
        if appendix_index is not None:
            order_ok = order_ok and ref_index < appendix_index
        if ack_index is not None and appendix_index is not None:
            order_ok = order_ok and appendix_index < ack_index
        elif ack_index is not None:
            order_ok = order_ok and ref_index < ack_index
    make_result(
        results,
        "section_order",
        "PASS" if order_ok else "MANUAL_REVIEW",
        "文档顺序已符合当前口径。" if order_ok else "文档顺序缺项或顺序不符合当前口径。",
        cn_index=cn_index,
        en_index=en_index,
        toc_index=toc_index,
        body_index=body_index,
        ref_index=ref_index,
        appendix_index=appendix_index,
        ack_index=ack_index,
    )

    fake_cover_markers = ["华南师范大学", "本科毕业论文", "封面"]
    first_texts = [text for _, _, text in paragraphs[:6]]
    fake_cover = any(marker in " ".join(first_texts) for marker in fake_cover_markers) and (cn_index is None or cn_index > 1)
    make_result(results, "official_cover_absence", "PASS" if not fake_cover else "MANUAL_REVIEW", "未发现伪造学校正式封面。" if not fake_cover else "文档前部存在疑似正式封面文案。", leading_paragraphs=first_texts)

    make_result(results, "notes_support", "NOT_SUPPORTED", "注释编号、页末注 / 篇末注规范当前仍需人工复核。", reason="当前工具只提供基础注释章节输出，不自动保证校规级注释排版。")
    make_result(results, "figure_table_captions", "NOT_SUPPORTED", "图题、表题位置与编号规则当前仍需人工复核。", reason="复杂图表对象不会在所有输入场景下自动重建为校规级题注。")

    return ComplianceReport(path=str(path), results=results)


def main() -> None:
    parser = argparse.ArgumentParser(description="Check SCNU thesis Word export compliance.")
    parser.add_argument("docx", type=Path, help="Path to exported .docx file")
    parser.add_argument("--json", action="store_true", help="Print JSON report")
    args = parser.parse_args()

    report = check_docx(args.docx)
    if args.json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        return

    print(f"检查文件: {report.path}")
    print(f"摘要: {report.summary}")
    for item in report.results:
        print(f"[{item.status}] {item.id}: {item.message}")
        if item.details:
            print(json.dumps(item.details, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
