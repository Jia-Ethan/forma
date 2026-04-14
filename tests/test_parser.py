from pathlib import Path

from backend.app.contracts import CapabilityFlags
from backend.app.services.parse import detect_heading, normalize_text_input, normalized_from_paragraphs, parse_docx_file, split_keywords
from backend.app.services.precheck import run_precheck

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "sample-thesis.docx"
COMPLEX_FIXTURE = Path(__file__).resolve().parents[1] / "examples" / "compliance" / "sample-docx-complex.docx"


def capabilities():
    return CapabilityFlags(docx_export=True, profile="undergraduate")


def test_parse_docx_extracts_title_and_expected_sections():
    thesis = parse_docx_file(FIXTURE, capabilities())
    assert thesis.metadata.title == "基于结构化映射的本科论文生成示例"
    assert thesis.abstract_cn.content
    assert thesis.abstract_en.content
    assert thesis.references.items
    assert thesis.acknowledgements
    assert thesis.appendix


def test_parse_docx_detects_complex_table_feature():
    thesis = parse_docx_file(COMPLEX_FIXTURE, capabilities())
    assert "tables" in thesis.source_features
    precheck = run_precheck(thesis)
    assert any(issue.code == "SOURCE_FEATURE_TABLES" for issue in precheck.issues)


def test_text_normalize_adds_missing_abstract_warnings_and_blocks_precheck():
    thesis = normalize_text_input("# 引言\n\n正文内容。" * 60, capabilities())
    assert thesis.body_sections
    assert "未识别到中文摘要，可在下一步补充。" in thesis.warnings
    assert "未识别到外文摘要，可在下一步补充。" in thesis.warnings

    precheck = run_precheck(thesis)
    assert precheck.summary.blocking_count >= 2
    assert any(issue.code == "TITLE_MISSING" for issue in precheck.issues)
    assert any(issue.code == "ABSTRACT_EN_MISSING" for issue in precheck.issues)


def test_detect_heading_rejects_numbered_reference_entries_and_sentence_like_list_items():
    assert detect_heading("1. 作者. 论文题目[J]. 期刊, 2024.", None) == (False, "", 0)
    assert detect_heading("1. 本研究采用问卷法开展实证分析。", None) == (False, "", 0)
    assert detect_heading("1.1 研究背景", None) == (True, "研究背景", 2)


def test_normalized_paragraphs_keep_numbered_reference_entries_in_reference_section():
    thesis = normalized_from_paragraphs(
        [
            ("基于结构化映射的本科论文生成示例", None),
            ("1 绪论", None),
            ("这是足够长的正文内容。 " * 40, None),
            ("参考文献", None),
            ("1. 作者. 论文题目[J]. 期刊, 2024.", None),
            ("2. 第二条文献[M]. 出版社, 2023.", None),
        ],
        "text",
        capabilities(),
        source_features=[],
    )

    assert thesis.references.items == [
        "1. 作者. 论文题目[J]. 期刊, 2024.",
        "2. 第二条文献[M]. 出版社, 2023.",
    ]
    assert [(section.level, section.title) for section in thesis.body_sections] == [(1, "绪论")]


def test_split_keywords_supports_common_english_keyword_prefixes():
    for raw in ["Keyword: alpha, beta", "Keywords: alpha, beta", "Key words: alpha, beta"]:
        body, keywords = split_keywords(f"This is abstract.\n{raw}", english=True)
        assert body == "This is abstract."
        assert keywords == ["alpha", "beta"]
