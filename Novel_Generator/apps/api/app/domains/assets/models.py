import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.core.database import Base
from app.core.enums import AssetSourceType, CharacterCardType, ConfirmStatus, LockStatus

JsonType = JSON().with_variant(JSONB, "postgresql")


class CharacterCard(Base):
    __tablename__ = "character_cards"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("novel_projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    card_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default=CharacterCardType.PERSON
    )
    profile_json: Mapped[dict[str, Any]] = mapped_column(JsonType, nullable=False, default=dict)
    tags: Mapped[list[str]] = mapped_column(JsonType, nullable=False, default=list)
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


class ThemeProfile(Base):
    __tablename__ = "theme_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("novel_projects.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    genre: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    theme: Mapped[str] = mapped_column(Text, nullable=False, default="")
    target_readers: Mapped[str] = mapped_column(Text, nullable=False, default="")
    narrative_style: Mapped[str] = mapped_column(Text, nullable=False, default="")
    emotional_tone: Mapped[str] = mapped_column(Text, nullable=False, default="")
    pleasure_points: Mapped[str] = mapped_column(Text, nullable=False, default="")
    forbidden_content: Mapped[str] = mapped_column(Text, nullable=False, default="")
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


class WorldSetting(Base):
    __tablename__ = "world_settings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("novel_projects.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    background_json: Mapped[dict[str, Any]] = mapped_column(JsonType, nullable=False, default=dict)
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


class Outline(Base):
    __tablename__ = "outlines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("novel_projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    plot_nodes_json: Mapped[list[Any]] = mapped_column(JsonType, nullable=False, default=list)
    character_arcs_json: Mapped[list[Any]] = mapped_column(JsonType, nullable=False, default=list)
    ending_direction: Mapped[str] = mapped_column(Text, nullable=False, default="")
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


class Volume(Base):
    __tablename__ = "volumes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("novel_projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    outline_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("outlines.id", ondelete="SET NULL"), nullable=True
    )
    volume_no: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    stage_goal: Mapped[str] = mapped_column(Text, nullable=False, default="")
    main_conflict: Mapped[str] = mapped_column(Text, nullable=False, default="")
    key_events_json: Mapped[list[Any]] = mapped_column(JsonType, nullable=False, default=list)
    involved_characters: Mapped[list[str]] = mapped_column(JsonType, nullable=False, default=list)
    emotional_rhythm: Mapped[str] = mapped_column(Text, nullable=False, default="")
    previous_relation: Mapped[str] = mapped_column(Text, nullable=False, default="")
    next_relation: Mapped[str] = mapped_column(Text, nullable=False, default="")
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
