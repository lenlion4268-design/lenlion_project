from datetime import datetime

from pydantic import BaseModel, Field

from app.core.enums import ConfirmStatus, ReadinessStage, ReviewAction, ReviewTargetType


class ReviewRequest(BaseModel):
    target_type: ReviewTargetType
    target_id: str = Field(min_length=1, max_length=36)
    comment: str | None = None
    operator_id: str | None = None


class ReviewResponse(BaseModel):
    target_type: ReviewTargetType
    target_id: str
    confirm_status: ConfirmStatus
    lock_status: str
    action: ReviewAction
    review_record_id: str


class ReviewRecordResponse(BaseModel):
    id: str
    project_id: str
    target_type: ReviewTargetType
    target_id: str
    action: ReviewAction
    operator_id: str | None
    comment: str | None
    before_status: ConfirmStatus
    after_status: ConfirmStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class ReadinessMissingItem(BaseModel):
    target_type: ReviewTargetType
    target_id: str | None = None
    label: str
    reason: str


class ReadinessResponse(BaseModel):
    project_id: str
    target_stage: ReadinessStage
    ready: bool
    missing_items: list[ReadinessMissingItem]
    blocked_reasons: list[str]
