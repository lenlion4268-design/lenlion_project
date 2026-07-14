import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.core.database import Base
from app.core.enums import AssetSourceType, ConfirmStatus, LockStatus, ReferenceWorkStatus, StyleAnalysisJobStatus

JsonType = JSON


class ReferenceWork(Base):
    __tablename__ = "reference_works"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("novel_projects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    author: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    format: Mapped[str] = mapped_column(String(20), nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    source_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default=AssetSourceType.REFERENCE_PARSE
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=ReferenceWorkStatus.UPLOADED)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ReferenceSample(Base):
    __tablename__ = "reference_samples"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    reference_work_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("reference_works.id", ondelete="CASCADE"), nullable=False, index=True
    )
    label: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    char_offset: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class StyleProfile(Base):
    __tablename__ = "style_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("novel_projects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    reference_work_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("reference_works.id", ondelete="CASCADE"), nullable=False
    )
    author: Mapped[str] = mapped_column(String(255), nullable=False)
    reference_title: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    voice_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    profile_json: Mapped[dict[str, Any]] = mapped_column(JsonType, nullable=False, default=dict)
    skill_markdown: Mapped[str] = mapped_column(Text, nullable=False, default="")
    confirm_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default=ConfirmStatus.DRAFT
    )
    lock_status: Mapped[str] = mapped_column(String(20), nullable=False, default=LockStatus.UNLOCKED)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class StyleAnalysisJob(Base):
    __tablename__ = "style_analysis_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("novel_projects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    reference_work_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("reference_works.id", ondelete="CASCADE"), nullable=False
    )
    style_profile_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("style_profiles.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=StyleAnalysisJobStatus.QUEUED
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    queue_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
