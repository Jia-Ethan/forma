from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class CoverFields(BaseModel):
    title: str = ""
    advisor: str = ""
    student_name: str = ""
    student_id: str = ""
    school: str = "华南师范大学"
    department: str = ""
    major: str = ""
    class_name: str = ""
    graduation_time: str = ""


class SummarySection(BaseModel):
    content: str = ""
    keywords: list[str] = Field(default_factory=list)


class BodySection(BaseModel):
    id: str
    level: int = 1
    title: str = ""
    content: str = ""

    @field_validator("level")
    @classmethod
    def clamp_level(cls, value: int) -> int:
        return min(max(value, 1), 4)


class ReferenceItem(BaseModel):
    raw_text: str = ""
    normalized_text: str = ""
    detected_type: str = ""


class AppendixSection(BaseModel):
    id: str
    title: str = ""
    content: str = ""


class SourceFeatures(BaseModel):
    table_count: int = 0
    image_count: int = 0
    footnote_count: int = 0
    textbox_count: int = 0
    shape_count: int = 0
    field_count: int = 0
    rich_run_count: int = 0


class CapabilityFlags(BaseModel):
    docx_export: bool = True
    profile: Literal["undergraduate"] = "undergraduate"


class SourceSpan(BaseModel):
    file_id: str | None = None
    source_document_id: str | None = None
    page: int | None = None
    paragraph_index: int | None = None
    block_index: int | None = None
    char_start: int | None = None
    char_end: int | None = None
    bbox: list[float] | None = None
    extraction_method: str = "unknown"


class ProvenanceRecord(BaseModel):
    source: Literal["user_upload", "user_edit", "parser", "agent_proposal", "confirmed_proposal", "system"] = "parser"
    actor: str = "system"
    proposal_id: str | None = None
    approval_id: str | None = None
    note: str = ""


class ThesisComment(BaseModel):
    id: str
    block_id: str | None = None
    author: str = ""
    content: str = ""
    source_span: SourceSpan | None = None
    resolved: bool = False


class FormatRisk(BaseModel):
    id: str
    block_id: str | None = None
    code: str
    severity: Literal["blocking", "warning", "info"] = "warning"
    message: str
    source: str = ""


class NormalizedBlock(BaseModel):
    id: str
    kind: Literal["cover", "abstract_cn", "abstract_en", "keywords", "body", "references", "appendices", "acknowledgements", "notes"] = "body"
    title: str = ""
    content: str = ""
    level: int = 1
    source_spans: list[SourceSpan] = Field(default_factory=list)
    provenance: list[ProvenanceRecord] = Field(default_factory=list)
    confidence: float = 1.0
    revision_id: str | None = None
    confirmed: bool = False
    generated_by_agent: bool = False

    @field_validator("confidence")
    @classmethod
    def clamp_confidence(cls, value: float) -> float:
        return min(max(value, 0.0), 1.0)


class NormalizedThesis(BaseModel):
    schema_version: Literal["2"] = "2"
    revision_id: str | None = None
    source_type: Literal["docx", "text", "story2paper", "pdf", "image", "reference", "project"] = "text"
    cover: CoverFields = Field(default_factory=CoverFields)
    abstract_cn: SummarySection = Field(default_factory=SummarySection)
    abstract_en: SummarySection = Field(default_factory=SummarySection)
    body_sections: list[BodySection] = Field(default_factory=list)
    references: list[ReferenceItem] = Field(default_factory=list)
    appendices: list[AppendixSection] = Field(default_factory=list)
    acknowledgements: str = ""
    notes: str = ""
    warnings: list[str] = Field(default_factory=list)
    manual_review_flags: list[str] = Field(default_factory=list)
    missing_sections: list[str] = Field(default_factory=list)
    source_features: SourceFeatures = Field(default_factory=SourceFeatures)
    capabilities: CapabilityFlags = Field(default_factory=CapabilityFlags)
    blocks: list[NormalizedBlock] = Field(default_factory=list)
    source_spans: list[SourceSpan] = Field(default_factory=list)
    provenance: list[ProvenanceRecord] = Field(default_factory=list)
    confidence: float = 1.0
    comments: list[ThesisComment] = Field(default_factory=list)
    format_risks: list[FormatRisk] = Field(default_factory=list)

    @model_validator(mode="after")
    def populate_v2_blocks(self) -> "NormalizedThesis":
        if self.blocks:
            return self

        blocks: list[NormalizedBlock] = []
        if self.abstract_cn.content.strip() or self.abstract_cn.keywords:
            blocks.append(
                NormalizedBlock(
                    id="abstract-cn",
                    kind="abstract_cn",
                    title="中文摘要",
                    content=self.abstract_cn.content,
                    confidence=0.9,
                )
            )
        if self.abstract_en.content.strip() or self.abstract_en.keywords:
            blocks.append(
                NormalizedBlock(
                    id="abstract-en",
                    kind="abstract_en",
                    title="Abstract",
                    content=self.abstract_en.content,
                    confidence=0.9,
                )
            )
        for section in self.body_sections:
            blocks.append(
                NormalizedBlock(
                    id=section.id,
                    kind="body",
                    title=section.title,
                    content=section.content,
                    level=section.level,
                    confidence=0.9,
                )
            )
        for index, item in enumerate(self.references, start=1):
            blocks.append(
                NormalizedBlock(
                    id=f"reference-{index}",
                    kind="references",
                    title=f"参考文献 {index}",
                    content=item.normalized_text or item.raw_text,
                    confidence=0.85,
                )
            )
        for appendix in self.appendices:
            blocks.append(
                NormalizedBlock(
                    id=appendix.id,
                    kind="appendices",
                    title=appendix.title,
                    content=appendix.content,
                    confidence=0.85,
                )
            )
        if self.acknowledgements.strip():
            blocks.append(
                NormalizedBlock(
                    id="acknowledgements",
                    kind="acknowledgements",
                    title="致谢",
                    content=self.acknowledgements,
                    confidence=0.85,
                )
            )
        if self.notes.strip():
            blocks.append(
                NormalizedBlock(
                    id="notes",
                    kind="notes",
                    title="注释",
                    content=self.notes,
                    confidence=0.8,
                )
            )
        self.blocks = blocks
        return self


class ServiceLimits(BaseModel):
    max_docx_size_bytes: int
    max_text_precheck_chars: int = 80_000


class HealthResponse(BaseModel):
    ok: bool = True
    app_env: str
    template: str
    capabilities: CapabilityFlags
    limits: ServiceLimits


class TextPrecheckRequest(BaseModel):
    text: str


class PrecheckIssue(BaseModel):
    id: str
    code: str
    severity: Literal["blocking", "warning", "info"]
    block: Literal[
        "cover",
        "abstract_cn",
        "abstract_en",
        "keywords",
        "body",
        "references",
        "appendices",
        "acknowledgements",
        "notes",
        "complex_elements",
    ]
    title: str
    message: str
    block_id: str | None = None
    source_span: SourceSpan | None = None
    rule_source_id: str | None = None
    suggested_action: str | None = None


class PreviewBlock(BaseModel):
    key: Literal[
        "cover",
        "abstract_cn",
        "abstract_en",
        "keywords",
        "body",
        "references",
        "appendices",
        "acknowledgements",
        "notes",
        "complex_elements",
    ]
    label: str
    status: Literal["ok", "warning", "blocking"]
    preview: str
    issue_ids: list[str] = Field(default_factory=list)


class PrecheckSummary(BaseModel):
    can_confirm: bool
    blocking_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    blocking_message: str = ""
    warning_message: str = ""


class PrecheckResponse(BaseModel):
    thesis: NormalizedThesis
    summary: PrecheckSummary
    issues: list[PrecheckIssue] = Field(default_factory=list)
    preview_blocks: list[PreviewBlock] = Field(default_factory=list)
    export_token: str | None = None
    expires_at: datetime | None = None
