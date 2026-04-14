import pytest

from backend.app.contracts import BodySection
from backend.app.services.export import extract_header_title, strip_subtitle_for_header


@pytest.mark.parametrize(
    ("raw_title", "expected"),
    [
        ("主标题：副标题", "主标题"),
        ("Main Title: Subtitle", "Main Title"),
        ("主标题——副标题", "主标题"),
        ("主标题 - 副标题", "主标题"),
        ("主标题 | 副标题", "主标题"),
        ("主标题（副标题）", "主标题"),
        ("主标题(副标题)", "主标题"),
        ("主标题：Subtitle", "主标题"),
        ("Main Title——副标题", "Main Title"),
    ],
)
def test_strip_subtitle_for_header_handles_common_subtitle_patterns(raw_title, expected):
    assert strip_subtitle_for_header(raw_title) == expected


@pytest.mark.parametrize(
    ("raw_title", "expected"),
    [
        ("面向复杂系统的研究（2026版）", "面向复杂系统的研究（2026版）"),
        ("人工智能导论(AI)", "人工智能导论(AI)"),
        ("A Study of A:B Testing", "A Study of A:B Testing"),
        ("不含副题的单行标题", "不含副题的单行标题"),
    ],
)
def test_strip_subtitle_for_header_stays_conservative_when_signal_is_weak(raw_title, expected):
    assert strip_subtitle_for_header(raw_title) == expected


def test_extract_header_title_uses_first_line_and_truncates():
    raw_title = "主标题：副标题\n第二行说明" + "很长" * 40
    result = extract_header_title(raw_title, max_length=12)
    assert result == "主标题"


@pytest.mark.parametrize(
    ("level", "expected"),
    [
        (2, "1.1."),
        (3, "1.1.1."),
        (4, "1.1.1.1."),
    ],
)
def test_section_number_backfills_missing_parent_levels(level, expected):
    from backend.app.services.export import section_number

    counters = [0, 0, 0, 0]
    result = section_number(BodySection(id="section", level=level, title="标题", content="正文"), counters)
    assert result == expected


def test_section_number_preserves_existing_ancestors_when_jump_level_occurs():
    from backend.app.services.export import section_number

    counters = [2, 0, 0, 0]
    result = section_number(BodySection(id="section", level=3, title="标题", content="正文"), counters)
    assert result == "2.1.1."
