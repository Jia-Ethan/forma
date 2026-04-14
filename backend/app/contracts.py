from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


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


class NormalizedThesis(BaseModel):
    source_type: Literal["docx", "text"] = "text"
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


class ServiceLimits(BaseModel):
    max_docx_size_bytes: int


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
