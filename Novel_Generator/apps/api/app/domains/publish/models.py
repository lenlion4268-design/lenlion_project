import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.enums import DeliveryStatus, PublicationStatus, PublishChannel


class Publication(Base):
    __tablename__ = "publications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("novel_projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    volume_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("volumes.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    format: Mapped[str] = mapped_column(String(20), nullable=False, default="markdown")
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=PublicationStatus.PUBLISHED
    )
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    chapter_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    channel: Mapped[str] = mapped_column(String(20), nullable=False, default=PublishChannel.LOCAL)
    delivery_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=DeliveryStatus.SKIPPED
    )
    delivery_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    external_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
