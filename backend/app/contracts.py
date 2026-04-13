from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class MetadataFields(BaseModel):
    title: str = ""
    author_name: str = ""
    student_id: str = ""
    department: str = ""
    major: str = ""
    class_name: str = ""
    advisor_name: str = ""
    submission_date: str = ""


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
        return min(max(value, 1), 3)


class ReferenceSection(BaseModel):
    items: list[str] = Field(default_factory=list)


class CapabilityFlags(BaseModel):
    docx_export: bool = True
    profile: Literal["undergraduate"] = "undergraduate"


class NormalizedThesis(BaseModel):
    source_type: Literal["docx", "text"] = "text"
    metadata: MetadataFields = Field(default_factory=MetadataFields)
    abstract_cn: SummarySection = Field(default_factory=SummarySection)
    abstract_en: SummarySection = Field(default_factory=SummarySection)
    body_sections: list[BodySection] = Field(default_factory=list)
    references: ReferenceSection = Field(default_factory=ReferenceSection)
    acknowledgements: str = ""
    appendix: str = ""
    warnings: list[str] = Field(default_factory=list)
    parse_errors: list[str] = Field(default_factory=list)
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
    block: Literal["title", "abstract_cn", "abstract_en", "keywords", "body", "references", "acknowledgements", "appendix", "metadata"]
    title: str
    message: str


class PreviewBlock(BaseModel):
    key: Literal["title", "abstract_cn", "abstract_en", "keywords", "body", "references", "acknowledgements", "appendix", "metadata"]
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
