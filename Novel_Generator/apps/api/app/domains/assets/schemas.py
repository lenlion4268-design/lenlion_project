from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.core.enums import (
    AssetSourceType,
    CharacterCardType,
    ConfirmStatus,
    LockStatus,
)


class CharacterProfile(BaseModel):
    personality: str = ""
    abilities: str = ""
    goals: str = ""
    weaknesses: str = ""
    experiences: str = ""
    identity: str = ""
    faction: str = ""
    organization: str = ""


class CharacterCardCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    card_type: CharacterCardType = CharacterCardType.PERSON
    profile_json: CharacterProfile = Field(default_factory=CharacterProfile)
    tags: list[str] = Field(default_factory=list)
    source_type: AssetSourceType = AssetSourceType.MANUAL


class CharacterCardUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    card_type: CharacterCardType | None = None
    profile_json: CharacterProfile | None = None
    tags: list[str] | None = None


class CharacterCardResponse(BaseModel):
    id: str
    project_id: str
    name: str
    card_type: CharacterCardType
    profile_json: dict[str, Any]
    tags: list[str]
    source_type: AssetSourceType
    confirm_status: ConfirmStatus
    lock_status: LockStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CharacterCardListResponse(BaseModel):
    items: list[CharacterCardResponse]
    total: int


class ThemeProfileUpsert(BaseModel):
    genre: str = ""
    theme: str = ""
    target_readers: str = ""
    narrative_style: str = ""
    emotional_tone: str = ""
    pleasure_points: str = ""
    forbidden_content: str = ""


class ThemeProfileResponse(BaseModel):
    id: str
    project_id: str
    genre: str
    theme: str
    target_readers: str
    narrative_style: str
    emotional_tone: str
    pleasure_points: str
    forbidden_content: str
    confirm_status: ConfirmStatus
    lock_status: LockStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WorldBackground(BaseModel):
    era: str = ""
    geography: str = ""
    institutions: str = ""
    power_system: str = ""
    historical_events: str = ""
    society: str = ""
    technology_level: str = ""
    culture: str = ""
    conflicts: str = ""


class WorldSettingUpsert(BaseModel):
    background_json: WorldBackground = Field(default_factory=WorldBackground)


class WorldSettingResponse(BaseModel):
    id: str
    project_id: str
    background_json: dict[str, Any]
    confirm_status: ConfirmStatus
    lock_status: LockStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OutlineCreate(BaseModel):
    title: str = Field(default="", max_length=255)
    summary: str = ""
    plot_nodes_json: list[Any] = Field(default_factory=list)
    character_arcs_json: list[Any] = Field(default_factory=list)
    ending_direction: str = ""


class OutlineResponse(BaseModel):
    id: str
    project_id: str
    title: str
    summary: str
    plot_nodes_json: list[Any]
    character_arcs_json: list[Any]
    ending_direction: str
    confirm_status: ConfirmStatus
    lock_status: LockStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OutlineListResponse(BaseModel):
    items: list[OutlineResponse]
    total: int


class VolumeCreate(BaseModel):
    outline_id: str | None = None
    volume_no: int = Field(default=1, ge=1)
    title: str = Field(default="", max_length=255)
    stage_goal: str = ""
    main_conflict: str = ""
    key_events_json: list[Any] = Field(default_factory=list)
    involved_characters: list[str] = Field(default_factory=list)
    emotional_rhythm: str = ""
    previous_relation: str = ""
    next_relation: str = ""


class VolumeResponse(BaseModel):
    id: str
    project_id: str
    outline_id: str | None
    volume_no: int
    title: str
    stage_goal: str
    main_conflict: str
    key_events_json: list[Any]
    involved_characters: list[str]
    emotional_rhythm: str
    previous_relation: str
    next_relation: str
    confirm_status: ConfirmStatus
    lock_status: LockStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class VolumeListResponse(BaseModel):
    items: list[VolumeResponse]
    total: int
