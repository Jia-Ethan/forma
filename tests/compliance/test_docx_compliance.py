from __future__ import annotations

from pathlib import Path

import pytest

from backend.app.contracts import CapabilityFlags
from backend.app.services.export import export_docx
from backend.app.services.parse import normalize_text_input, parse_docx_file
from backend.app.services.precheck import run_precheck
from scripts.check_docx_compliance import check_docx

EXAMPLES = Path(__file__).resolve().parents[2] / "examples" / "compliance"


def capabilities() -> CapabilityFlags:
    return CapabilityFlags(docx_export=True, profile="undergraduate")


def load_example(source_kind: str, path: Path):
    if source_kind == "text":
        return normalize_text_input(path.read_text(encoding="utf-8"), capabilities())
    return parse_docx_file(path, capabilities())


@pytest.mark.parametrize(
    ("source_kind", "name", "expected_warning_codes"),
    [
        ("text", "sample-text-basic.md", {"ABSTRACT_CN_LENGTH_RECOMMENDED", "COVER_FIELDS_MISSING"}),
        ("docx", "sample-docx-basic.docx", {"ABSTRACT_CN_LENGTH_RECOMMENDED", "COVER_FIELDS_MISSING"}),
        ("docx", "sample-docx-complex.docx", {"ABSTRACT_CN_LENGTH_RECOMMENDED", "COVER_FIELDS_MISSING", "SOURCE_FEATURE_TABLES"}),
    ],
)
def test_compliance_examples_run_full_pipeline(source_kind: str, name: str, expected_warning_codes: set[str], tmp_path: Path):
    thesis = load_example(source_kind, EXAMPLES / name)

    precheck = run_precheck(thesis)
    assert precheck.summary.blocking_count == 0
    warning_codes = {item.code for item in precheck.issues if item.severity == "warning"}
    assert expected_warning_codes.issubset(warning_codes)

    output_path = tmp_path / f"{Path(name).stem}-export.docx"
    output_path.write_bytes(export_docx(thesis))

    report = check_docx(output_path)
    statuses = {item.id: item.status for item in report.results}
    assert statuses["page_size"] == "PASS"
    assert statuses["margins_gutter"] == "PASS"
    assert statuses["cn_abstract_style"] == "PASS"
    assert statuses["en_abstract_style"] == "PASS"
    assert statuses["toc_field"] == "PASS"
    assert statuses["header_title"] == "PASS"
    assert statuses["section_order"] == "PASS"
    assert statuses["official_cover_absence"] == "PASS"
    assert statuses["notes_support"] == "NOT_SUPPORTED"
    assert statuses["figure_table_captions"] == "NOT_SUPPORTED"
    assert report.summary["MANUAL_REVIEW"] == 0
    assert report.summary["NOT_SUPPORTED"] == 2


def test_example_assets_exist():
    assert (EXAMPLES / "sample-text-basic.md").exists()
    assert (EXAMPLES / "sample-docx-basic.docx").exists()
    assert (EXAMPLES / "sample-docx-complex.docx").exists()
