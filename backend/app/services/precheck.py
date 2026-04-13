from __future__ import annotations

import re
from collections import defaultdict

from ..contracts import NormalizedThesis, PrecheckIssue, PrecheckResponse, PrecheckSummary, PreviewBlock

BLOCK_ORDER = [
    ("title", "题目"),
    ("abstract_cn", "中文摘要"),
    ("abstract_en", "外文摘要"),
    ("keywords", "关键词"),
    ("body", "正文结构"),
    ("references", "参考文献"),
    ("acknowledgements", "致谢"),
    ("appendix", "附录"),
    ("metadata", "封面字段"),
]

GENERIC_TITLES = {"正文", "无标题", "论文题目", "待补充论文题目"}
METADATA_FIELDS = [
    ("author_name", "学生姓名"),
    ("student_id", "学号"),
    ("department", "学院"),
    ("major", "专业"),
    ("advisor_name", "指导老师"),
    ("submission_date", "提交日期"),
    ("class_name", "班级"),
]
COMPLEX_FEATURE_MESSAGES = {
    "tables": "检测到表格内容，当前导出为重新排版模式，表格题名与版式需人工复核。",
    "images": "检测到图片内容，当前导出不保证图题位置与环绕方式完全保真。",
    "footnotes": "检测到脚注内容，当前不自动保证页末注编号、版式与学校规范完全一致。",
    "endnotes": "检测到篇末注内容，当前不自动保证篇末注编号与版式完全一致。",
}


def compact_text(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def preview_text(text: str, *, fallback: str, limit: int = 110) -> str:
    compact = " ".join((text or "").strip().split())
    if not compact:
        return fallback
    return compact[:limit] + ("..." if len(compact) > limit else "")


def english_word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", text or ""))


def block_preview(thesis: NormalizedThesis, block_key: str) -> str:
    if block_key == "title":
        return thesis.metadata.title.strip() or "未识别到标题"
    if block_key == "abstract_cn":
        return preview_text(thesis.abstract_cn.content, fallback="未识别到中文摘要")
    if block_key == "abstract_en":
        return preview_text(thesis.abstract_en.content, fallback="未识别到外文摘要")
    if block_key == "keywords":
        cn = "，".join(thesis.abstract_cn.keywords)
        en = ", ".join(thesis.abstract_en.keywords)
        if cn and en:
            return f"中文：{cn} | English: {en}"
        if cn:
            return f"中文：{cn}"
        if en:
            return f"English: {en}"
        return "未识别到关键词"
    if block_key == "body":
        if not thesis.body_sections:
            return "未识别到正文结构"
        titles = " / ".join(section.title.strip() or "正文" for section in thesis.body_sections[:4])
        suffix = f"（共 {len(thesis.body_sections)} 个结构块）"
        feature_text = f"；复杂元素：{', '.join(thesis.source_features)}" if thesis.source_features else ""
        return f"{titles}{' ...' if len(thesis.body_sections) > 4 else ''} {suffix}{feature_text}".strip()
    if block_key == "references":
        if not thesis.references.items:
            return "未识别到参考文献"
        return preview_text("\n".join(thesis.references.items[:3]), fallback="未识别到参考文献")
    if block_key == "acknowledgements":
        return preview_text(thesis.acknowledgements, fallback="未提供致谢")
    if block_key == "appendix":
        return preview_text(thesis.appendix, fallback="未提供附录")
    filled = [label for field, label in METADATA_FIELDS if getattr(thesis.metadata, field).strip()]
    return f"正式统一封面需另行套用；已识别 {len(filled)}/{len(METADATA_FIELDS)} 项字段"


def issue(issue_id: str, code: str, severity: str, block: str, title: str, message: str) -> PrecheckIssue:
    return PrecheckIssue(
        id=issue_id,
        code=code,
        severity=severity,  # type: ignore[arg-type]
        block=block,  # type: ignore[arg-type]
        title=title,
        message=message,
    )


def run_precheck(thesis: NormalizedThesis) -> PrecheckResponse:
    issues: list[PrecheckIssue] = []

    title = thesis.metadata.title.strip()
    abstract_cn = compact_text(thesis.abstract_cn.content)
    abstract_en = compact_text(thesis.abstract_en.content)
    abstract_en_words = english_word_count(thesis.abstract_en.content)
    body_length = sum(len(compact_text(section.content)) for section in thesis.body_sections)
    references_count = len(thesis.references.items)

    if not title or title in GENERIC_TITLES:
        issues.append(issue("title-missing", "TITLE_MISSING", "blocking", "title", "题目缺失", "未识别到可用论文题目，无法生成合规页眉与正文审查稿。"))

    if len(abstract_cn) < 80:
        issues.append(
            issue(
                "abstract-cn-missing",
                "ABSTRACT_CN_MISSING",
                "blocking",
                "abstract_cn",
                "中文摘要缺失",
                "中文摘要缺失，或有效内容明显不足，暂时不能继续导出。",
            )
        )
    elif not 250 <= len(abstract_cn) <= 300:
        issues.append(
            issue(
                "abstract-cn-length",
                "ABSTRACT_CN_LENGTH_RECOMMENDED",
                "warning",
                "abstract_cn",
                "中文摘要长度需复核",
                "中文摘要建议控制在 250–300 字，目前未落在推荐区间内。",
            )
        )

    if not abstract_en:
        issues.append(issue("abstract-en-missing", "ABSTRACT_EN_MISSING", "blocking", "abstract_en", "外文摘要缺失", "外文摘要是当前导出稿的必备部分，暂时不能继续导出。"))
    elif abstract_en_words > 250:
        issues.append(issue("abstract-en-length", "ABSTRACT_EN_LENGTH_RECOMMENDED", "warning", "abstract_en", "外文摘要长度需复核", "外文摘要建议不超过 250 个实词，请在导出后人工复核。"))

    if not thesis.body_sections:
        issues.append(issue("body-missing", "BODY_MISSING", "blocking", "body", "正文主体缺失", "未识别到正文结构，无法生成论文主文。"))
    elif body_length < 400:
        issues.append(issue("body-short", "BODY_TOO_SHORT", "blocking", "body", "正文内容不足", "正文有效内容过短，暂时不能继续导出。"))

    if references_count == 0:
        issues.append(issue("references-missing", "REFERENCES_MISSING", "blocking", "references", "参考文献缺失", "未识别到参考文献内容，暂时不能继续导出。"))

    if not thesis.abstract_cn.keywords:
        issues.append(issue("keywords-cn-missing", "KEYWORDS_CN_MISSING", "warning", "keywords", "中文关键词缺失", "未识别到中文关键词，导出后将无法满足摘要格式要求。"))

    if not thesis.abstract_en.keywords:
        issues.append(issue("keywords-en-missing", "KEYWORDS_EN_MISSING", "warning", "keywords", "外文关键词缺失", "未识别到外文关键词，导出后请人工补足。"))

    if thesis.abstract_cn.keywords and not (3 <= len(thesis.abstract_cn.keywords) <= 8):
        issues.append(issue("keywords-cn-count", "KEYWORDS_CN_COUNT", "warning", "keywords", "中文关键词数量异常", "中文关键词数量建议控制在 3–8 个之间。"))

    if thesis.abstract_en.keywords and not (3 <= len(thesis.abstract_en.keywords) <= 8):
        issues.append(issue("keywords-en-count", "KEYWORDS_EN_COUNT", "warning", "keywords", "外文关键词数量异常", "外文关键词数量建议控制在 3–8 个之间。"))

    if thesis.abstract_cn.keywords and thesis.abstract_en.keywords and len(thesis.abstract_cn.keywords) != len(thesis.abstract_en.keywords):
        issues.append(issue("keywords-pairing", "KEYWORDS_ALIGNMENT", "warning", "keywords", "中外文关键词未对齐", "外文关键词数量应与中文关键词相对应，请人工复核。"))

    missing_metadata = [label for field, label in METADATA_FIELDS if not getattr(thesis.metadata, field).strip()]
    if missing_metadata:
        issues.append(
            issue(
                "metadata-missing",
                "COVER_FIELDS_MISSING",
                "warning",
                "metadata",
                "封面字段未补全",
                f"系统不会自动生成学校正式封面；以下字段仍未识别：{'、'.join(missing_metadata)}。",
            )
        )

    level_jumps = [
        (prev.level, current.level)
        for prev, current in zip(thesis.body_sections, thesis.body_sections[1:])
        if current.level - prev.level > 1
    ]
    if level_jumps:
        issues.append(issue("body-levels", "BODY_LEVELS_UNSTABLE", "warning", "body", "章节层级不稳定", "章节层级存在跳级，目录层级与编号可能需要人工调整。"))

    if not thesis.appendix.strip():
        issues.append(issue("appendix-missing", "APPENDIX_MISSING", "warning", "appendix", "附录未识别", "未识别到附录内容；若论文包含附录，请在导出后补充。"))

    if not thesis.acknowledgements.strip():
        issues.append(issue("acknowledgements-missing", "ACKNOWLEDGEMENTS_MISSING", "warning", "acknowledgements", "致谢未识别", "未识别到致谢内容；若论文需要致谢，请在导出后补充。"))

    if thesis.notes.strip() or any(feature in thesis.source_features for feature in {"footnotes", "endnotes"}):
        issues.append(issue("notes-review", "NOTES_MANUAL_REVIEW", "warning", "body", "注释需人工复核", "当前导出不自动保证页末注 / 篇末注编号与版式完全符合学校规范。"))

    for feature in thesis.source_features:
        message = COMPLEX_FEATURE_MESSAGES.get(feature)
        if message:
            issues.append(issue(f"feature-{feature}", f"SOURCE_FEATURE_{feature.upper()}", "warning", "body", "复杂内容需人工复核", message))

    if thesis.source_type == "docx":
        issues.append(issue("docx-source", "DOCX_SOURCE_INFO", "info", "body", "当前为 Word 上传", "系统会重新排版生成正文审查稿，不承诺原始复杂版式完全保真。"))
    else:
        issues.append(issue("text-source", "TEXT_SOURCE_INFO", "info", "body", "当前为纯文本输入", "纯文本模式不会恢复原始图片、脚注与复杂版式。"))

    issues.append(issue("toc-info", "TOC_AUTO_GENERATED", "info", "body", "目录将自动生成", "导出稿会插入可更新目录字段，打开 Word 后请更新目录。"))
    issues.append(issue("cover-info", "OFFICIAL_COVER_EXTERNAL", "info", "metadata", "正式封面需另行套用", "当前工具不生成学校统一正式封面，只导出正文审查稿。"))
    issues.append(issue("body-section-count", "BODY_SECTION_COUNT", "info", "body", "章节识别概览", f"当前识别到 {len(thesis.body_sections)} 个正文结构块。"))
    issues.append(issue("export-profile", "DOCX_EXPORT_PROFILE", "info", "metadata", "导出配置", "导出将按 SC-TH 本科论文正文审查稿模板生成。"))

    grouped: dict[str, list[PrecheckIssue]] = defaultdict(list)
    for item in issues:
        grouped[item.block].append(item)

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
        blocking_message = f"当前仍有 {blocking_count} 项合规阻塞项，暂时无法确认导出。"
    else:
        blocking_message = "当前未发现阻塞项，可以继续导出正文审查稿。"

    warning_message = f"另有 {warning_count} 项警告需要在导出后复核。"

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
