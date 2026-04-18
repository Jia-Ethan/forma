from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


def now_utc() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc, onupdate=now_utc, nullable=False)


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(200), default="Local User", nullable=False)


class ThesisProject(Base, TimestampMixin):
    __tablename__ = "thesis_projects"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("users.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(300), default="未命名论文项目", nullable=False)
    school: Mapped[str] = mapped_column(String(80), default="scnu", nullable=False)
    degree_level: Mapped[str] = mapped_column(String(80), default="undergraduate", nullable=False)
    template_profile: Mapped[str] = mapped_column(String(120), default="scnu-undergraduate", nullable=False)
    rule_set_id: Mapped[str] = mapped_column(String(120), default="scnu-undergraduate-2025", nullable=False)
    department: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    major: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    advisor: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    student_name: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    student_id: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    writing_stage: Mapped[str] = mapped_column(String(80), default="draft", nullable=False)
    privacy_mode: Mapped[str] = mapped_column(String(80), default="local_only", nullable=False)
    remote_provider_allowed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False)
    current_version_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class ProjectFile(Base, TimestampMixin):
    __tablename__ = "project_files"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), ForeignKey("thesis_projects.id"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(60), default="docx", nullable=False)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    storage_key: Mapped[str] = mapped_column(String(1000), nullable=False)
    parser: Mapped[str] = mapped_column(String(120), default="registry", nullable=False)
    source_label: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class SourceDocument(Base, TimestampMixin):
    __tablename__ = "source_documents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), ForeignKey("thesis_projects.id"), nullable=False, index=True)
    file_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("project_files.id"), nullable=True)
    kind: Mapped[str] = mapped_column(String(80), default="upload", nullable=False)
    title: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    ledger: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class ThesisVersion(Base, TimestampMixin):
    __tablename__ = "thesis_versions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), ForeignKey("thesis_projects.id"), nullable=False, index=True)
    parent_version_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    label: Mapped[str] = mapped_column(String(200), default="baseline", nullable=False)
    thesis: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_by: Mapped[str] = mapped_column(String(80), default="system", nullable=False)


class NormalizedBlockRecord(Base, TimestampMixin):
    __tablename__ = "normalized_blocks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), ForeignKey("thesis_projects.id"), nullable=False, index=True)
    version_id: Mapped[str] = mapped_column(String(64), ForeignKey("thesis_versions.id"), nullable=False, index=True)
    block_id: Mapped[str] = mapped_column(String(120), nullable=False)
    kind: Mapped[str] = mapped_column(String(60), nullable=False)
    title: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    content: Mapped[str] = mapped_column(Text, default="", nullable=False)
    source_spans: Mapped[list] = mapped_column(JSON, default=list, nullable=False)


class Issue(Base, TimestampMixin):
    __tablename__ = "issues"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), ForeignKey("thesis_projects.id"), nullable=False, index=True)
    version_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("thesis_versions.id"), nullable=True, index=True)
    code: Mapped[str] = mapped_column(String(120), nullable=False)
    severity: Mapped[str] = mapped_column(String(40), nullable=False)
    block: Mapped[str] = mapped_column(String(80), nullable=False)
    block_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    source_span: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    rule_source_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    suggested_action: Mapped[str | None] = mapped_column(String(300), nullable=True)


class Proposal(Base, TimestampMixin):
    __tablename__ = "proposals"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), ForeignKey("thesis_projects.id"), nullable=False, index=True)
    version_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("thesis_versions.id"), nullable=True, index=True)
    target_block_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    operation: Mapped[str] = mapped_column(String(80), default="comment", nullable=False)
    before: Mapped[str] = mapped_column(Text, default="", nullable=False)
    after: Mapped[str] = mapped_column(Text, default="", nullable=False)
    reason: Mapped[str] = mapped_column(Text, default="", nullable=False)
    risk: Mapped[str] = mapped_column(Text, default="", nullable=False)
    source_refs: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    affects_export: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="pending", nullable=False)


class Approval(Base, TimestampMixin):
    __tablename__ = "approvals"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    proposal_id: Mapped[str] = mapped_column(String(64), ForeignKey("proposals.id"), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(String(64), ForeignKey("thesis_projects.id"), nullable=False, index=True)
    decision: Mapped[str] = mapped_column(String(40), nullable=False)
    resulting_version_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    actor: Mapped[str] = mapped_column(String(80), default="local-user", nullable=False)


class AgentRun(Base, TimestampMixin):
    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("thesis_projects.id"), nullable=True, index=True)
    kind: Mapped[str] = mapped_column(String(80), default="parse", nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="running", nullable=False)
    current_agent: Mapped[str | None] = mapped_column(String(120), nullable=True)
    result: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)


class AgentEvent(Base, TimestampMixin):
    __tablename__ = "agent_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(64), ForeignKey("agent_runs.id"), nullable=False, index=True)
    project_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("thesis_projects.id"), nullable=True, index=True)
    type: Mapped[str] = mapped_column(String(80), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)


class ExportRecord(Base, TimestampMixin):
    __tablename__ = "exports"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), ForeignKey("thesis_projects.id"), nullable=False, index=True)
    version_id: Mapped[str] = mapped_column(String(64), ForeignKey("thesis_versions.id"), nullable=False, index=True)
    format: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="completed", nullable=False)
    storage_key: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    filename: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    summary: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)


class ProviderConfig(Base, TimestampMixin):
    __tablename__ = "provider_configs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    model: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    base_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    encrypted_api_key: Mapped[str] = mapped_column(Text, default="", nullable=False)
    allow_local: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verification_status: Mapped[str] = mapped_column(String(40), default="untested", nullable=False)
    verification_message: Mapped[str] = mapped_column(Text, default="", nullable=False)
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("thesis_projects.id"), nullable=True, index=True)
    actor: Mapped[str] = mapped_column(String(80), default="system", nullable=False)
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    target_type: Mapped[str] = mapped_column(String(80), default="", nullable=False)
    target_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
