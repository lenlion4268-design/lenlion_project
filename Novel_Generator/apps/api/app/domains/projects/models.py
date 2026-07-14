import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.enums import ProjectMode, ProjectStage, ProjectStatus


class NovelProject(Base):
    __tablename__ = "novel_projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    genre: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    mode: Mapped[str] = mapped_column(String(20), nullable=False, default=ProjectMode.LONG)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=ProjectStatus.ACTIVE)
    current_stage: Mapped[str] = mapped_column(
        String(30), nullable=False, default=ProjectStage.CHARACTERS
    )
    active_style_profile_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("style_profiles.id", ondelete="SET NULL", use_alter=True),
        nullable=True,
    )
    owner_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
