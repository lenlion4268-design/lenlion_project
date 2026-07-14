from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.enums import ReadinessStage
from app.domains.assets.status_service import AssetStatusService
from app.domains.projects.repository import ProjectRepository
from app.domains.review.schemas import ReadinessResponse, ReviewRequest, ReviewResponse
from app.domains.review.service import ReadinessService, ReviewService

router = APIRouter(prefix=f"{settings.api_prefix}", tags=["review"])


def get_review_service(db: Session = Depends(get_db)) -> ReviewService:
    return ReviewService(db, ProjectRepository(db), AssetStatusService(db))


def get_readiness_service(db: Session = Depends(get_db)) -> ReadinessService:
    return ReadinessService(db, ProjectRepository(db))


@router.post("/review/confirm", response_model=ReviewResponse)
def confirm_asset(
    data: ReviewRequest,
    service: ReviewService = Depends(get_review_service),
) -> ReviewResponse:
    return service.confirm(data)


@router.post("/review/lock", response_model=ReviewResponse)
def lock_asset(
    data: ReviewRequest,
    service: ReviewService = Depends(get_review_service),
) -> ReviewResponse:
    return service.lock(data)


@router.post("/review/reject", response_model=ReviewResponse)
def reject_asset(
    data: ReviewRequest,
    service: ReviewService = Depends(get_review_service),
) -> ReviewResponse:
    return service.reject(data)


@router.post("/review/unlock", response_model=ReviewResponse)
def unlock_asset(
    data: ReviewRequest,
    service: ReviewService = Depends(get_review_service),
) -> ReviewResponse:
    return service.unlock(data)


@router.get(
    "/projects/{project_id}/readiness/{target_stage}",
    response_model=ReadinessResponse,
)
def get_readiness(
    project_id: str,
    target_stage: ReadinessStage,
    outline_id: str | None = Query(default=None),
    volume_id: str | None = Query(default=None),
    service: ReadinessService = Depends(get_readiness_service),
) -> ReadinessResponse:
    return service.check(
        project_id,
        target_stage,
        outline_id=outline_id,
        volume_id=volume_id,
    )
