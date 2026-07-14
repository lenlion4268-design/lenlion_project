from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

WORKSPACE_SETTINGS_ID = "default"


class WorkspaceSettings(Base):
    __tablename__ = "workspace_settings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=WORKSPACE_SETTINGS_ID)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    pen_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_provider: Mapped[str] = mapped_column(String(30), nullable=False, default="mock")
    ai_model: Mapped[str] = mapped_column(String(100), nullable=False, default="mock-writer")
    openai_base_url: Mapped[str] = mapped_column(
        String(500), nullable=False, default="https://api.openai.com/v1"
    )
    openai_api_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_model_outline: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ai_model_volume: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ai_model_chapter: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ai_model_profile_fast: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ai_model_profile_quality: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ai_request_timeout_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=120.0)
    ai_batch_max_chapters: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    default_model_profile: Mapped[str] = mapped_column(String(20), nullable=False, default="default")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
