from pathlib import Path
from zipfile import ZipFile
import io

from backend.app.contracts import NormalizedThesis
from backend.app.services.export import export_docx, truncate_header_title
from scripts.check_docx_compliance import BANNED_PLACEHOLDERS, build_report


def sample_payload():
    return {
        "source_type": "text",
        "cover": {
            "title": "结构化映射示例论文：副标题不会进入页眉——这是一个用于验证页眉截断规则的超长主标题",
            "advisor": "李老师",
            "student_name": "张三",
            "student_id": "2020123456",
            "school": "华南师范大学",
            "department": "计算机学院",
            "major": "网络工程",
            "class_name": "1班",
            "graduation_time": "2026年6月",
        },
        "abstract_cn": {
            "content": "本文展示结构化映射后的论文导出流程，并说明如何在统一中间结构下生成符合学校规范的本科论文 Word 文件。",
            "keywords": ["论文模板", "结构化映射", "Word 导出"],
        },
        "abstract_en": {
            "content": "This thesis demonstrates a standards-driven Word export pipeline for SCNU undergraduate theses.",
            "keywords": ["thesis", "word export", "mapping"],
        },
        "body_sections": [
            {"id": "section-1", "level": 1, "title": "引言", "content": "本章介绍系统目标与规范仲裁逻辑。" * 8},
            {"id": "section-2", "level": 2, "title": "结构设计", "content": "系统统一将输入映射为中间结构，再渲染为规范驱动的 Word 文档。" * 6},
        ],
        "references": [
            {"raw_text": "【1】示例作者. 论文模板实践[J].", "normalized_text": "示例作者. 论文模板实践[J].", "detected_type": "J"},
        ],
        "appendices": [{"id": "appendix-1", "title": "附录 A 测试样例", "content": "这里是附录内容。"}],
        "acknowledgements": "感谢导师的指导。",
        "notes": "",
        "warnings": [],
        "manual_review_flags": [],
        "missing_sections": [],
        "source_features": {
            "table_count": 0,
            "image_count": 0,
            "footnote_count": 0,
            "textbox_count": 0,
            "shape_count": 0,
            "field_count": 0,
            "rich_run_count": 0,
        },
        "capabilities": {"docx_export": True, "profile": "undergraduate"},
    }


def export_archive(payload: dict) -> ZipFile:
    thesis = NormalizedThesis.model_validate(payload)
    blob = export_docx(thesis)
    return ZipFile(io.BytesIO(blob))


def test_compliance_script_passes_on_primary_export(tmp_path: Path):
    thesis = NormalizedThesis.model_validate(sample_payload())
    target = tmp_path / "sample.docx"
    target.write_bytes(export_docx(thesis))

    report = build_report(target)

    assert report["status"] == "PASS"
    assert ("upperRoman", "1") in report["section_formats"]
    assert ("decimal", "1") in report["section_formats"]


def test_missing_sections_export_keeps_blank_structure_without_placeholders():
    payload = sample_payload()
    payload["abstract_en"] = {"content": "", "keywords": []}
    payload["appendices"] = []
    payload["acknowledgements"] = ""

    archive = export_archive(payload)
    document_xml = archive.read("word/document.xml").decode("utf-8")

    assert "Abstract" in document_xml
    assert "附录" in document_xml
    assert "致谢" in document_xml
    for token in BANNED_PLACEHOLDERS:
        assert token not in document_xml


def test_long_title_header_is_truncated_without_subtitle():
    payload = sample_payload()
    archive = export_archive(payload)
    header_xml = "\n".join(
        archive.read(name).decode("utf-8")
        for name in archive.namelist()
        if name.startswith("word/header")
    )
    expected = truncate_header_title(payload["cover"]["title"])

    assert expected in header_xml
    assert "副标题不会进入页眉" not in header_xml
    assert "——" not in header_xml


def test_reference_rendering_uses_normalized_text_and_hanging_indent():
    archive = export_archive(sample_payload())
    document_xml = archive.read("word/document.xml").decode("utf-8")

    assert "示例作者. 论文模板实践[J]." in document_xml
    assert "【1】示例作者" not in document_xml
    assert 'w:hanging="420"' in document_xml or 'w:hanging="419"' in document_xml
