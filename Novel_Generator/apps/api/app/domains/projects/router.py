from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.enums import ProjectStatus
from app.domains.projects.repository import ProjectRepository
from app.domains.projects.schemas import (
    ProjectCreate,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdate,
)
from app.domains.projects.service import ProjectService

router = APIRouter(prefix=f"{settings.api_prefix}/projects", tags=["projects"])


def get_project_service(db: Session = Depends(get_db)) -> ProjectService:
    return ProjectService(ProjectRepository(db))


@router.post("", response_model=ProjectResponse, status_code=201)
def create_project(
    data: ProjectCreate,
    service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    return service.create_project(data)


@router.get("", response_model=ProjectListResponse)
def list_projects(
    status: ProjectStatus | None = Query(default=None),
    service: ProjectService = Depends(get_project_service),
) -> ProjectListResponse:
    return service.list_projects(status=status)


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: str,
    service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    return service.get_project(project_id)


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: str,
    data: ProjectUpdate,
    service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    return service.update_project(project_id, data)
