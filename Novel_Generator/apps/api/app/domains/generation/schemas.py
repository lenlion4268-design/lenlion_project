from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.core.enums import (
    ConfirmStatus,
    ExecutionMode,
    GenerationJobStatus,
    LockStatus,
    ModelProfile,
    ReadinessStage,
)


class GenerationRequest(BaseModel):
    target_stage: ReadinessStage
    outline_id: str | None = None
    volume_id: str | None = None
    batch_count: int = Field(default=1, ge=1, le=10)
    model_profile: ModelProfile = ModelProfile.DEFAULT
    async_mode: bool = False


class GenerationRunResponse(BaseModel):
    jobs: list["GenerationJobResponse"]
    total: int


class GenerationJobResponse(BaseModel):
    id: str
    project_id: str
    target_stage: ReadinessStage
    outline_id: str | None
    volume_id: str | None
    status: GenerationJobStatus
    provider: str
    model_profile: ModelProfile
    model_name: str | None
    execution_mode: ExecutionMode
    queue_task_id: str | None = None
    result_type: str | None
    result_id: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class GenerationJobListResponse(BaseModel):
    items: list[GenerationJobResponse]
    total: int


class ChapterUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    content: str | None = None


class ChapterResponse(BaseModel):
    id: str
    project_id: str
    volume_id: str
    generation_job_id: str | None
    chapter_no: int
    title: str
    content: str
    word_count: int
    source_type: str
    confirm_status: ConfirmStatus
    lock_status: LockStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChapterListResponse(BaseModel):
    items: list[ChapterResponse]
    total: int


class OutlineDraft(BaseModel):
    title: str
    summary: str
    plot_nodes_json: list[Any]
    character_arcs_json: list[Any]
    ending_direction: str


class VolumeDraft(BaseModel):
    volume_no: int
    title: str
    stage_goal: str
    main_conflict: str
    key_events_json: list[Any]
    involved_characters: list[str]
    emotional_rhythm: str
    previous_relation: str
    next_relation: str
    outline_id: str | None


class ChapterDraft(BaseModel):
    chapter_no: int
    title: str
    content: str


class ManuscriptExportResponse(BaseModel):
    project_id: str
    volume_id: str | None
    format: str
    chapter_count: int
    content: str
    file_size: int | None = None
