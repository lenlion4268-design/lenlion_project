import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.enums import AssetSourceType, ConfirmStatus, GenerationJobStatus, LockStatus


class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("novel_projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_stage: Mapped[str] = mapped_column(String(30), nullable=False)
    outline_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    volume_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=GenerationJobStatus.QUEUED
    )
    provider: Mapped[str] = mapped_column(String(30), nullable=False, default="mock")
    model_profile: Mapped[str] = mapped_column(String(20), nullable=False, default="default")
    model_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    execution_mode: Mapped[str] = mapped_column(String(10), nullable=False, default="sync")
    queue_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    result_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    result_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Chapter(Base):
    __tablename__ = "chapters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("novel_projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    volume_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("volumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    generation_job_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("generation_jobs.id", ondelete="SET NULL"), nullable=True
    )
    chapter_no: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    source_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default=AssetSourceType.MANUAL
    )
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
