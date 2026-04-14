from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from zipfile import ZipFile

BANNED_PLACEHOLDERS = [
    "待补充论文题目",
    "未填写",
    "请在 Word 中右键更新目录",
]


def read_docx_parts(path: Path) -> dict[str, str]:
    with ZipFile(path) as archive:
        return {
            name: archive.read(name).decode("utf-8", errors="ignore")
            for name in archive.namelist()
            if name.endswith(".xml") or name.endswith(".rels")
        }


def normalize_for_search(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def gather_document_text(document_xml: str) -> str:
    return "".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", document_xml))


def collect_section_formats(document_xml: str) -> list[tuple[str | None, str | None]]:
    formats: list[tuple[str | None, str | None]] = []
    for match in re.finditer(r"<w:sectPr\b.*?</w:sectPr>", document_xml, flags=re.DOTALL):
        sect = match.group(0)
        pg = re.search(r"<w:pgNumType\b([^>]*)/>", sect)
        if not pg:
            formats.append((None, None))
            continue
        attrs = pg.group(1)
        fmt = re.search(r'w:fmt="([^"]+)"', attrs)
        start = re.search(r'w:start="([^"]+)"', attrs)
        formats.append((fmt.group(1) if fmt else None, start.group(1) if start else None))
    return formats


def build_report(path: Path) -> dict[str, object]:
    if not path.exists() or path.suffix.lower() != ".docx":
        return {"status": "NOT_SUPPORTED", "reasons": ["文件不存在或不是 .docx。"]}

    parts = read_docx_parts(path)
    document_xml = parts.get("word/document.xml", "")
    styles_xml = parts.get("word/styles.xml", "")
    settings_xml = parts.get("word/settings.xml", "")
    headers = {name: xml for name, xml in parts.items() if name.startswith("word/header")}
    footers = {name: xml for name, xml in parts.items() if name.startswith("word/footer")}

    text = normalize_for_search(gather_document_text(document_xml))
    reasons: list[str] = []
    manual_review: list[str] = []

    if not document_xml:
        return {"status": "NOT_SUPPORTED", "reasons": ["文档主体 XML 缺失。"]}

    if not all(token in text for token in ["华南师范大学", "本科毕业论文", "论文题目", "指导教师", "学生姓名", "学号", "学院", "专业", "班级"]):
        reasons.append("正式封面字段未完整落位。")

    order_tokens = ["摘要", "Abstract", "目录", "参考文献", "附录", "致谢"]
    order_positions = []
    for token in order_tokens:
        position = text.find(normalize_for_search(token))
        if position == -1:
            reasons.append(f"缺少章节：{token}")
        order_positions.append(position)
    filtered_positions = [position for position in order_positions if position >= 0]
    if filtered_positions != sorted(filtered_positions):
        reasons.append("摘要 / 目录 / 参考文献 / 附录 / 致谢顺序不符合新主线。")

    if 'TOC\\o"1-4"\\h\\z\\u' not in normalize_for_search(document_xml):
        reasons.append("目录字段缺失。")
    if 'w:updateFieldsw:val="true"' not in normalize_for_search(settings_xml):
        reasons.append("Word 自动更新目录字段设置缺失。")

    section_formats = collect_section_formats(document_xml)
    if not any(fmt == "upperRoman" and start == "1" for fmt, start in section_formats):
        reasons.append("前置部分未检测到大写罗马页码分节。")
    if not any(fmt == "decimal" and start == "1" for fmt, start in section_formats):
        reasons.append("正文未检测到阿拉伯页码重启分节。")

    if not headers:
        reasons.append("页眉文件缺失。")
    if not footers:
        reasons.append("页脚文件缺失。")
    if footers and not any("PAGE" in xml for xml in footers.values()):
        reasons.append("页脚页码字段缺失。")

    normalized_styles = normalize_for_search(styles_xml)
    if "Heading1" not in styles_xml and 'w:namew:val="heading1"' not in normalized_styles:
        reasons.append("标题样式缺失。")
    if 'toc1' not in normalized_styles:
        reasons.append("目录项样式缺失。")

    for token in BANNED_PLACEHOLDERS:
        if token in text:
            reasons.append(f"检测到历史占位词：{token}")

    if "<w:tbl" in document_xml:
        manual_review.append("输出中包含表格。")
    if "word/footnotes.xml" in parts:
        manual_review.append("输出中包含脚注或尾注。")

    if reasons:
        status = "NOT_SUPPORTED"
    elif manual_review:
        status = "MANUAL_REVIEW"
    else:
        status = "PASS"

    return {
        "status": status,
        "reasons": reasons,
        "manual_review": manual_review,
        "checked_file": str(path),
        "section_formats": section_formats,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check SCNU thesis DOCX compliance.")
    parser.add_argument("docx_path", type=Path)
    args = parser.parse_args()
    report = build_report(args.docx_path)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] != "NOT_SUPPORTED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
