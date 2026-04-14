from __future__ import annotations

import re
from collections import defaultdict

from ..contracts import NormalizedThesis, PrecheckIssue, PrecheckResponse, PrecheckSummary, PreviewBlock

BLOCK_ORDER = [
    ("cover", "正式封面"),
    ("abstract_cn", "中文摘要"),
    ("abstract_en", "英文摘要"),
    ("keywords", "关键词"),
    ("body", "正文结构"),
    ("references", "参考文献"),
    ("appendices", "附录"),
    ("acknowledgements", "致谢"),
    ("notes", "注释"),
    ("complex_elements", "复杂元素"),
]

COVER_FIELD_LABELS = [
    ("title", "论文题目"),
    ("advisor", "指导教师"),
    ("student_name", "学生姓名"),
    ("student_id", "学号"),
    ("department", "学院"),
    ("major", "专业"),
    ("class_name", "班级"),
    ("graduation_time", "毕业时间"),
]


def compact_text(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def preview_text(text: str, *, fallback: str, limit: int = 110) -> str:
    compact = " ".join((text or "").strip().split())
    if not compact:
        return fallback
    return compact[:limit] + ("..." if len(compact) > limit else "")


def issue(issue_id: str, code: str, severity: str, block: str, title: str, message: str) -> PrecheckIssue:
    return PrecheckIssue(
        id=issue_id,
        code=code,
        severity=severity,  # type: ignore[arg-type]
        block=block,  # type: ignore[arg-type]
        title=title,
        message=message,
    )


def block_preview(thesis: NormalizedThesis, block_key: str) -> str:
    if block_key == "cover":
        filled = [label for field, label in COVER_FIELD_LABELS if getattr(thesis.cover, field).strip()]
        return f"已识别 {len(filled)}/{len(COVER_FIELD_LABELS)} 项：{'、'.join(filled) if filled else '封面字段留白'}"
    if block_key == "abstract_cn":
        return preview_text(thesis.abstract_cn.content, fallback="将保留中文摘要章节留白")
    if block_key == "abstract_en":
        return preview_text(thesis.abstract_en.content, fallback="将保留英文摘要章节留白")
    if block_key == "keywords":
        cn = "，".join(thesis.abstract_cn.keywords)
        en = ", ".join(thesis.abstract_en.keywords)
        if cn and en:
            return f"中文：{cn} | English: {en}"
        if cn:
            return f"中文：{cn}"
        if en:
            return f"English: {en}"
        return "关键词将按空白位保留"
    if block_key == "body":
        titles = " / ".join(section.title.strip() or "正文" for section in thesis.body_sections[:4])
        suffix = f"（共 {len(thesis.body_sections)} 个结构块）"
        return f"{titles}{' ...' if len(thesis.body_sections) > 4 else ''} {suffix}".strip()
    if block_key == "references":
        if not thesis.references:
            return "将保留参考文献章节留白"
        return preview_text("\n".join(item.normalized_text or item.raw_text for item in thesis.references[:3]), fallback="将保留参考文献章节留白")
    if block_key == "appendices":
        if not thesis.appendices:
            return "将保留附录章节留白"
        titles = " / ".join(item.title.strip() or "附录" for item in thesis.appendices[:3])
        return f"{titles}{' ...' if len(thesis.appendices) > 3 else ''}"
    if block_key == "acknowledgements":
        return preview_text(thesis.acknowledgements, fallback="将保留致谢章节留白")
    if block_key == "notes":
        return preview_text(thesis.notes, fallback="未识别到注释章节")
    feature = thesis.source_features
    if not thesis.manual_review_flags:
        return "未检测到需人工复核的复杂元素"
    details = []
    if feature.table_count:
        details.append(f"表格 {feature.table_count}")
    if feature.image_count:
        details.append(f"图片 {feature.image_count}")
    if feature.footnote_count:
        details.append(f"脚注/尾注 {feature.footnote_count}")
    if feature.textbox_count or feature.shape_count:
        details.append("文本框/形状")
    if feature.field_count:
        details.append("原始字段")
    return "；".join(details) if details else "存在复杂元素，需人工复核"


def run_precheck(thesis: NormalizedThesis) -> PrecheckResponse:
    issues: list[PrecheckIssue] = []

    body_text_length = sum(len(compact_text(section.content)) for section in thesis.body_sections)
    if not thesis.body_sections or body_text_length == 0:
        issues.append(
            issue(
                "body-missing",
                "BODY_MISSING",
                "blocking",
                "body",
                "正文主体不足",
                "未识别到足够的正文内容，当前无法生成可用的论文主文。",
            )
        )

    missing_cover_fields = [label for field, label in COVER_FIELD_LABELS if not getattr(thesis.cover, field).strip()]
    if missing_cover_fields:
        issues.append(
            issue(
                "cover-fields-missing",
                "COVER_FIELDS_MISSING",
                "warning",
                "cover",
                "封面字段将留白",
                f"以下封面字段未识别，将按学校格式保留下划线或留白：{'、'.join(missing_cover_fields)}。",
            )
        )

    if not thesis.abstract_cn.content.strip():
        issues.append(issue("abstract-cn-missing", "ABSTRACT_CN_BLANK", "warning", "abstract_cn", "中文摘要将留白", "未识别到中文摘要，导出时会保留中文摘要章节空白区。"))
    if not thesis.abstract_en.content.strip():
        issues.append(issue("abstract-en-missing", "ABSTRACT_EN_BLANK", "warning", "abstract_en", "英文摘要将留白", "未识别到英文摘要，导出时会保留英文摘要章节空白区。"))
    if not thesis.abstract_cn.keywords:
        issues.append(issue("keywords-cn-missing", "KEYWORDS_CN_BLANK", "warning", "keywords", "中文关键词将留白", "未识别到中文关键词，导出时会保留关键词位置留白。"))
    if thesis.abstract_en.content.strip() and not thesis.abstract_en.keywords:
        issues.append(issue("keywords-en-missing", "KEYWORDS_EN_BLANK", "warning", "keywords", "英文关键词将留白", "已识别英文摘要，但未识别到英文关键词。"))

    if not thesis.references:
        issues.append(issue("references-missing", "REFERENCES_BLANK", "warning", "references", "参考文献将留白", "未识别到参考文献条目，导出时会保留参考文献章节空白区。"))
    if not thesis.appendices:
        issues.append(issue("appendices-missing", "APPENDICES_BLANK", "warning", "appendices", "附录将留白", "未识别到附录内容，导出时会保留附录章节空白区。"))
    if not thesis.acknowledgements.strip():
        issues.append(issue("acknowledgements-missing", "ACKNOWLEDGEMENTS_BLANK", "warning", "acknowledgements", "致谢将留白", "未识别到致谢内容，导出时会保留致谢章节空白区。"))
    if thesis.notes.strip():
        issues.append(issue("notes-present", "NOTES_PRESENT", "info", "notes", "检测到注释章节", "检测到显式注释章节，将按正文后、参考文献前的位置输出。"))

    if thesis.manual_review_flags:
        issues.append(
            issue(
                "complex-elements",
                "MANUAL_REVIEW_REQUIRED",
                "warning",
                "complex_elements",
                "复杂元素需人工复核",
                "检测到表格、图片、脚注或其他复杂 Word 元素，结构导出可继续，但结果需人工复核。",
            )
        )
    else:
        issues.append(issue("complex-elements-clear", "NO_COMPLEX_ELEMENTS", "info", "complex_elements", "复杂元素检查", "当前未检测到明显的复杂 Word 元素。"))

    level_jumps = [
        (prev.level, current.level)
        for prev, current in zip(thesis.body_sections, thesis.body_sections[1:])
        if current.level - prev.level > 1
    ]
    if level_jumps:
        issues.append(issue("body-levels", "BODY_LEVELS_UNSTABLE", "warning", "body", "章节层级不稳定", "正文标题层级存在跳级，系统会按保守策略归类，建议导出后人工复核。"))

    issues.append(
        issue(
            "body-section-count",
            "BODY_SECTION_COUNT",
            "info",
            "body",
            "章节识别概览",
            f"当前识别到 {len(thesis.body_sections)} 个正文章节块，将固定生成目录、分节和页码。",
        )
    )
    issues.append(
        issue(
            "export-profile",
            "DOCX_EXPORT_PROFILE",
            "info",
            "cover",
            "导出主线",
            "导出将按“学校规范 PDF > 学生手册补充 > main.pdf > 旧实现”的仲裁规则生成本科论文 Word 文件。",
        )
    )

    grouped: dict[str, list[PrecheckIssue]] = defaultdict(list)
    for current_issue in issues:
        grouped[current_issue.block].append(current_issue)

    preview_blocks: list[PreviewBlock] = []
    for key, label in BLOCK_ORDER:
        block_issues = grouped.get(key, [])
        status = "ok"
        if any(item.severity == "blocking" for item in block_issues):
            status = "blocking"
        elif any(item.severity == "warning" for item in block_issues):
            status = "warning"
        preview_blocks.append(
            PreviewBlock(
                key=key,  # type: ignore[arg-type]
                label=label,
                status=status,  # type: ignore[arg-type]
                preview=block_preview(thesis, key),
                issue_ids=[item.id for item in block_issues],
            )
        )

    blocking_count = sum(item.severity == "blocking" for item in issues)
    warning_count = sum(item.severity == "warning" for item in issues)
    info_count = sum(item.severity == "info" for item in issues)

    if blocking_count:
        blocking_message = f"当前仍有 {blocking_count} 项阻塞问题，暂时无法导出。"
    else:
        blocking_message = "结构基线已满足，可继续导出规范化 Word 文件。"

    if warning_count:
        warning_message = f"另有 {warning_count} 项警告，其中缺失章节会按留白位保留，复杂元素需人工复核。"
    else:
        warning_message = "当前没有额外警告。"

    return PrecheckResponse(
        thesis=thesis,
        summary=PrecheckSummary(
            can_confirm=blocking_count == 0,
            blocking_count=blocking_count,
            warning_count=warning_count,
            info_count=info_count,
            blocking_message=blocking_message,
            warning_message=warning_message,
        ),
        issues=issues,
        preview_blocks=preview_blocks,
    )
