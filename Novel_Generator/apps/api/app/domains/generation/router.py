from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse, Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.domains.assets.status_service import AssetStatusService
from app.domains.generation.export_service import ExportService
from app.domains.generation.repository import GenerationRepository
from app.domains.generation.schemas import (
    ChapterListResponse,
    ChapterResponse,
    ChapterUpdate,
    GenerationJobListResponse,
    GenerationJobResponse,
    GenerationRequest,
    GenerationRunResponse,
    ManuscriptExportResponse,
)
from app.domains.generation.service import GenerationService
from app.domains.projects.repository import ProjectRepository
from app.domains.review.service import ReadinessService

router = APIRouter(tags=["generation"])


def get_generation_service(db: Session = Depends(get_db)) -> GenerationService:
    return GenerationService(
        db,
        ProjectRepository(db),
        GenerationRepository(db),
        ReadinessService(db, ProjectRepository(db)),
        AssetStatusService(db),
    )


def get_export_service(db: Session = Depends(get_db)) -> ExportService:
    return ExportService(db, ProjectRepository(db), GenerationRepository(db))


@router.post(
    f"{settings.api_prefix}/projects/{{project_id}}/generation",
    response_model=GenerationRunResponse,
    status_code=201,
)
def create_generation_job(
    project_id: str,
    data: GenerationRequest,
    service: GenerationService = Depends(get_generation_service),
) -> GenerationRunResponse:
    return service.run_generation(project_id, data)


@router.get(
    f"{settings.api_prefix}/projects/{{project_id}}/generation/jobs",
    response_model=GenerationJobListResponse,
)
def list_generation_jobs(
    project_id: str,
    service: GenerationService = Depends(get_generation_service),
) -> GenerationJobListResponse:
    return service.list_jobs(project_id)


@router.get(
    f"{settings.api_prefix}/generation/jobs/{{job_id}}",
    response_model=GenerationJobResponse,
)
def get_generation_job(
    job_id: str,
    service: GenerationService = Depends(get_generation_service),
) -> GenerationJobResponse:
    return service.get_job(job_id)


@router.post(
    f"{settings.api_prefix}/generation/jobs/{{job_id}}/cancel",
    response_model=GenerationJobResponse,
)
def cancel_generation_job(
    job_id: str,
    service: GenerationService = Depends(get_generation_service),
) -> GenerationJobResponse:
    return service.cancel_job(job_id)


@router.get(
    f"{settings.api_prefix}/projects/{{project_id}}/chapters",
    response_model=ChapterListResponse,
)
def list_chapters(
    project_id: str,
    volume_id: str | None = Query(default=None),
    service: GenerationService = Depends(get_generation_service),
) -> ChapterListResponse:
    return service.list_chapters(project_id, volume_id=volume_id)


@router.get(
    f"{settings.api_prefix}/chapters/{{chapter_id}}",
    response_model=ChapterResponse,
)
def get_chapter(
    chapter_id: str,
    service: GenerationService = Depends(get_generation_service),
) -> ChapterResponse:
    return service.get_chapter(chapter_id)


@router.patch(
    f"{settings.api_prefix}/chapters/{{chapter_id}}",
    response_model=ChapterResponse,
)
def update_chapter(
    chapter_id: str,
    data: ChapterUpdate,
    service: GenerationService = Depends(get_generation_service),
) -> ChapterResponse:
    return service.update_chapter(chapter_id, data)


@router.get(
    f"{settings.api_prefix}/projects/{{project_id}}/export",
    response_model=ManuscriptExportResponse,
)
def export_manuscript_json(
    project_id: str,
    volume_id: str | None = Query(default=None),
    include_drafts: bool = Query(default=False),
    export_format: str = Query(default="markdown", alias="format"),
    service: ExportService = Depends(get_export_service),
) -> ManuscriptExportResponse:
    return service.export_manuscript(
        project_id,
        volume_id=volume_id,
        include_drafts=include_drafts,
        export_format=export_format,
    )


@router.get(
    f"{settings.api_prefix}/projects/{{project_id}}/export/download",
)
def export_manuscript_download(
    project_id: str,
    volume_id: str | None = Query(default=None),
    include_drafts: bool = Query(default=False),
    export_format: str = Query(default="markdown", alias="format"),
    service: ExportService = Depends(get_export_service),
) -> Response:
    export_file = service.build_export_file(
        project_id,
        volume_id=volume_id,
        include_drafts=include_drafts,
        export_format=export_format,
    )
    if isinstance(export_file.payload, bytes):
        return Response(
            content=export_file.payload,
            media_type=export_file.media_type,
            headers={"Content-Disposition": f'attachment; filename="{export_file.filename}"'},
        )
    return PlainTextResponse(
        content=export_file.payload,
        media_type=export_file.media_type,
        headers={"Content-Disposition": f'attachment; filename="{export_file.filename}"'},
    )
