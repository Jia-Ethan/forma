from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class SectionNode(BaseModel):
    kind: str
    title: str
    content: str


class DocumentParseResult(BaseModel):
    source_type: Literal["form", "docx"]
    metadata: dict[str, str] = Field(default_factory=dict)
    sections: list[SectionNode] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class GenerationArtifacts(BaseModel):
    job_id: str
    pdf_path: str | None = None
    texzip_path: str | None = None
    compile_log_path: str | None = None


class ThesisGenerationRequest(BaseModel):
    title: str
    author_name: str
    student_id: str
    department: str
    major: str
    class_name: str
    advisor_name: str
    submission_date: str
    abstract_cn: str
    abstract_en: str
    keywords_cn: str = ""
    keywords_en: str = ""
    body: str
    references: str = ""
    acknowledgements: str = ""
    appendix: str = ""

    @field_validator(
        "title",
        "author_name",
        "student_id",
        "department",
        "major",
        "class_name",
        "advisor_name",
        "submission_date",
        "abstract_cn",
        "abstract_en",
        "body",
    )
    @classmethod
    def non_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("字段不能为空")
        return value.strip()


class JobCreateResponse(BaseModel):
    job_id: str
    status: str


class TeXDependencyStatus(BaseModel):
    xelatex: bool
    kpsewhich: bool
    missing_styles: list[str] = Field(default_factory=list)


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    source_type: str
    template: str
    error_code: str | None = None
    error_message: str | None = None
    warnings: list[str] = Field(default_factory=list)
    sections: list[SectionNode] = Field(default_factory=list)
    artifacts: GenerationArtifacts | None = None
    compile_command: list[str] = Field(default_factory=list)
    output_dir: str | None = None
