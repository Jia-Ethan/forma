from pathlib import Path

from backend.app.contracts import CapabilityFlags
from backend.app.services.parse import normalize_text_input, parse_docx_file
from backend.app.services.precheck import run_precheck


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "sample-thesis.docx"
MISSING_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "missing-sections.docx"


def capabilities():
    return CapabilityFlags(docx_export=True, profile="undergraduate")


def test_parse_docx_extracts_cover_and_expected_sections():
    thesis = parse_docx_file(FIXTURE, capabilities())

    assert thesis.cover.title == "基于结构化映射的本科论文生成示例"
    assert thesis.abstract_cn.content
    assert thesis.abstract_en.content
    assert thesis.references
    assert thesis.appendices
    assert thesis.acknowledgements
    assert thesis.body_sections[0].title == "引言"


def test_parse_docx_tracks_missing_sections_without_fabrication():
    thesis = parse_docx_file(MISSING_FIXTURE, capabilities())

    assert "appendices" in thesis.missing_sections
    assert "acknowledgements" in thesis.missing_sections
    assert "cover.advisor" in thesis.missing_sections
    assert thesis.references[0].normalized_text == "示例作者. 规范化导出实践[J]."

    precheck = run_precheck(thesis)
    assert precheck.summary.can_confirm is True
    assert any(issue.code == "APPENDICES_BLANK" for issue in precheck.issues)
    assert any(issue.code == "ACKNOWLEDGEMENTS_BLANK" for issue in precheck.issues)


def test_text_normalize_keeps_missing_sections_as_warnings():
    thesis = normalize_text_input("# 引言\n\n正文内容。" * 20, capabilities())

    assert thesis.body_sections
    assert "abstract_cn" in thesis.missing_sections
    assert "references" in thesis.missing_sections
    assert "未识别到中文摘要，导出时会保留摘要章节留白。" in thesis.warnings

    precheck = run_precheck(thesis)
    assert precheck.summary.can_confirm is True
    assert precheck.summary.blocking_count == 0
    assert any(issue.code == "ABSTRACT_CN_BLANK" for issue in precheck.issues)


def test_docx_and_text_inputs_can_converge_to_same_semantics():
    docx_thesis = parse_docx_file(MISSING_FIXTURE, capabilities())
    text_thesis = normalize_text_input(
        "\n".join(
            [
                "论文题目：面向规范映射的本科论文导出基线",
                "学生姓名：张三",
                "学号：2020123456",
                "学院：计算机学院",
                "专业：网络工程",
                "摘要",
                "本文用于验证缺失章节时仍能保留结构留白，不自动补写不存在的内容。",
                "关键词：导出规范，章节映射，留白策略",
                "第一章 引言",
                "这里是引言正文，用于验证正文仍可被识别并导出。",
                "1.1 研究背景",
                "这里是研究背景，用于验证多级标题目录联动。",
                "参考文献",
                "【1】示例作者. 规范化导出实践[J].",
            ]
        ),
        capabilities(),
    )

    assert docx_thesis.cover.title == text_thesis.cover.title
    assert [section.title for section in docx_thesis.body_sections] == [section.title for section in text_thesis.body_sections]
    assert [item.normalized_text for item in docx_thesis.references] == [item.normalized_text for item in text_thesis.references]
    assert docx_thesis.missing_sections == text_thesis.missing_sections
