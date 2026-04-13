from pathlib import Path

from backend.app.contracts import CapabilityFlags
from backend.app.services.parse import normalize_text_input, parse_docx_file
from backend.app.services.precheck import run_precheck


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "sample-thesis.docx"


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


def test_text_normalize_adds_missing_abstract_warnings_and_blocks_precheck():
    thesis = normalize_text_input("# 引言\n\n正文内容。" * 60, capabilities())
    assert thesis.body_sections
    assert "未识别到中文摘要，可在下一步补充。" in thesis.warnings
    assert "未识别到 Abstract，可在下一步补充。" in thesis.warnings

    precheck = run_precheck(thesis)
    assert precheck.summary.blocking_count >= 2
    assert any(issue.code == "TITLE_MISSING" for issue in precheck.issues)
