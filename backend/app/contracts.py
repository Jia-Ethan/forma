from __future__ import annotations

from typing import Literal, Optional

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
    tex_zip: bool = True
    pdf: bool = False
    pdf_reason: Optional[str] = None


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


class TeXDependencyStatus(BaseModel):
    xelatex: bool
    kpsewhich: bool
    missing_styles: list[str] = Field(default_factory=list)


class ServiceLimits(BaseModel):
    max_docx_size_bytes: int


class HealthResponse(BaseModel):
    ok: bool = True
    app_env: str
    template: str
    capabilities: CapabilityFlags
    limits: ServiceLimits
    tex: TeXDependencyStatus


class TextNormalizeRequest(BaseModel):
    text: str
