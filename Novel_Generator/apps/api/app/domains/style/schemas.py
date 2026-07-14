from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class StyleVocabulary(BaseModel):
    language_register: str = Field(default="", alias="register")
    taboo: list[str] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class StyleProfileJson(BaseModel):
    pov: str = ""
    sentence_rhythm: str = ""
    dialogue_ratio: str = ""
    pacing: str = ""
    emotional_tone: str = ""
    vocabulary: StyleVocabulary = Field(default_factory=StyleVocabulary)
    techniques: list[str] = Field(default_factory=list)
    hooks: list[str] = Field(default_factory=list)
    example_excerpts: list[str] = Field(default_factory=list)


class ReferenceSampleResponse(BaseModel):
    id: str
    label: str
    content: str
    char_offset: int

    model_config = {"from_attributes": True}


class ReferenceWorkResponse(BaseModel):
    id: str
    project_id: str | None
    author: str
    title: str
    format: str
    word_count: int
    source_type: str
    status: str
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReferenceWorkDetailResponse(ReferenceWorkResponse):
    samples: list[ReferenceSampleResponse] = Field(default_factory=list)


class ReferenceWorkListResponse(BaseModel):
    items: list[ReferenceWorkResponse]
    total: int


class EpubInspectResponse(BaseModel):
    suggested_author: str | None = None
    suggested_title: str | None = None


class StyleAnalysisJobResponse(BaseModel):
    id: str
    project_id: str | None
    reference_work_id: str
    style_profile_id: str | None
    status: str
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class StyleProfileResponse(BaseModel):
    id: str
    project_id: str | None
    reference_work_id: str
    author: str
    reference_title: str
    name: str
    voice_summary: str
    profile_json: dict[str, Any]
    skill_markdown: str
    confirm_status: str
    lock_status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StyleProfileListResponse(BaseModel):
    items: list[StyleProfileResponse]
    total: int


class StyleProfileUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    voice_summary: str | None = None
    profile_json: dict[str, Any] | None = None
    skill_markdown: str | None = None


class ActiveStyleResponse(BaseModel):
    active_style_profile_id: str | None
    author: str | None = None
    name: str | None = None
