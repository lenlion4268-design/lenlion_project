from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse, Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.domains.generation.export_service import ExportService
from app.domains.generation.repository import GenerationRepository
from app.domains.publish.schemas import PublicationListResponse, PublicationResponse, PublishRequest
from app.domains.publish.service import PublishRepository, PublishService
from app.domains.projects.repository import ProjectRepository

router = APIRouter(tags=["publish"])


def get_publish_service(db: Session = Depends(get_db)) -> PublishService:
    return PublishService(
        db,
        ProjectRepository(db),
        PublishRepository(db),
        ExportService(db, ProjectRepository(db), GenerationRepository(db)),
    )


@router.post(
    f"{settings.api_prefix}/projects/{{project_id}}/publish",
    response_model=PublicationResponse,
    status_code=201,
)
def publish_manuscript(
    project_id: str,
    data: PublishRequest,
    service: PublishService = Depends(get_publish_service),
) -> PublicationResponse:
    return service.publish(project_id, data)


@router.get(
    f"{settings.api_prefix}/projects/{{project_id}}/publications",
    response_model=PublicationListResponse,
)
def list_publications(
    project_id: str,
    service: PublishService = Depends(get_publish_service),
) -> PublicationListResponse:
    return service.list_publications(project_id)


@router.get(
    f"{settings.api_prefix}/publications/{{publication_id}}",
    response_model=PublicationResponse,
)
def get_publication(
    publication_id: str,
    service: PublishService = Depends(get_publish_service),
) -> PublicationResponse:
    return service.get_publication(publication_id)


@router.post(
    f"{settings.api_prefix}/publications/{{publication_id}}/retry-delivery",
    response_model=PublicationResponse,
)
def retry_publication_delivery(
    publication_id: str,
    service: PublishService = Depends(get_publish_service),
) -> PublicationResponse:
    return service.retry_delivery(publication_id)


@router.get(
    f"{settings.api_prefix}/publications/{{publication_id}}/download",
)
def download_publication(
    publication_id: str,
    service: PublishService = Depends(get_publish_service),
) -> Response:
    payload, media_type, filename = service.read_publication_file(publication_id)
    if isinstance(payload, bytes):
        return Response(
            content=payload,
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    return PlainTextResponse(
        content=payload,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
