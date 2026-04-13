from pathlib import Path

from backend.app.contracts import BodySection, CapabilityFlags, MetadataFields, NormalizedThesis, ReferenceSection, SummarySection
from backend.app.services.export import export_docx
from scripts.check_docx_compliance import check_docx


EXAMPLES = Path(__file__).resolve().parents[2] / "examples" / "compliance"


def sample_thesis() -> NormalizedThesis:
    return NormalizedThesis(
        source_type="text",
        metadata=MetadataFields(title="合规检查样例论文"),
        abstract_cn=SummarySection(
            content="本文围绕华南师范大学本科毕业论文格式合规导出展开，目标是在极简输入主线上，把结构识别、规则预检、Word 样式输出和自动化合规检查串成一条稳定链路。系统不伪造学校正式封面，而是聚焦正文审查稿的结构和排版合规。通过统一页面设置、目录字段、页眉页脚、摘要样式和章节编号控制，导出结果可以更接近学校送审稿的格式基线。",
            keywords=["论文格式", "Word 导出", "合规检查"],
        ),
        abstract_en=SummarySection(
            content="This sample thesis presents a compliance-oriented export workflow for SCNU undergraduate theses. It focuses on structured parsing, precheck validation, Word styling, and repeatable compliance checks instead of pretending to generate the official printed cover.",
            keywords=["thesis format", "word export", "compliance check"],
        ),
        body_sections=[
            BodySection(id="s1", level=1, title="引言", content="本章说明项目背景、目标与本轮合规重构范围。" * 45),
            BodySection(id="s2", level=2, title="规则映射", content="规则映射用于把学校规范拆成页面设置、样式、目录、摘要、正文、参考文献和附录等可执行检查项。" * 30),
            BodySection(id="s3", level=3, title="自动验收", content="自动验收会在导出后检查页面尺寸、页边距、装订线、目录字段、关键样式和文档顺序。" * 20),
            BodySection(id="s4", level=4, title="人工抽检", content="人工抽检用于复核图表、注释和参考文献等暂不完全自动保证的部分。" * 16),
        ],
        notes="① 注释示例：当前版本仅提供基础注释章节输出，页末注需人工复核。",
        references=ReferenceSection(items=["【1】示例作者. 本科论文导出实践[J]. 示例期刊, 2026(1):1-10."]),
        appendix="附录 A 术语表\n\n这里给出补充说明。",
        acknowledgements="感谢导师和同学的帮助。",
        capabilities=CapabilityFlags(docx_export=True, profile="undergraduate"),
    )


def test_check_docx_reports_pass_for_core_compliance_items(tmp_path):
    output = tmp_path / "compliance-export.docx"
    output.write_bytes(export_docx(sample_thesis()))
    report = check_docx(output)
    statuses = {item.id: item.status for item in report.results}
    assert statuses["page_size"] == "PASS"
    assert statuses["margins_gutter"] == "PASS"
    assert statuses["style_catalog"] == "PASS"
    assert statuses["body_style"] == "PASS"
    assert statuses["cn_abstract_style"] == "PASS"
    assert statuses["en_abstract_style"] == "PASS"
    assert statuses["toc_field"] == "PASS"
    assert statuses["header_title"] == "PASS"
    assert statuses["header_font"] == "PASS"
    assert statuses["footer_page_field"] == "PASS"
    assert statuses["footer_font"] == "PASS"
    assert statuses["section_order"] == "PASS"
    assert statuses["official_cover_absence"] == "PASS"
    assert statuses["notes_support"] == "NOT_SUPPORTED"
    assert statuses["figure_table_captions"] == "NOT_SUPPORTED"


def test_example_assets_exist():
    assert (EXAMPLES / "sample-text-basic.md").exists()
    assert (EXAMPLES / "sample-docx-basic.docx").exists()
    assert (EXAMPLES / "sample-docx-complex.docx").exists()
