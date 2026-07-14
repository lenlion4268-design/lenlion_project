from datetime import datetime

from pydantic import BaseModel, Field

from app.core.enums import ProjectMode, ProjectStage, ProjectStatus


class ProjectCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    genre: str = Field(default="", max_length=100)
    mode: ProjectMode = ProjectMode.LONG


class ProjectUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    genre: str | None = Field(default=None, max_length=100)
    current_stage: ProjectStage | None = None
    status: ProjectStatus | None = None


class ProjectResponse(BaseModel):
    id: str
    title: str
    genre: str
    mode: ProjectMode
    status: ProjectStatus
    current_stage: ProjectStage
    active_style_profile_id: str | None = None
    owner_id: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectListResponse(BaseModel):
    items: list[ProjectResponse]
    total: int
