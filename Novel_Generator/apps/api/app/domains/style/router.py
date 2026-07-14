from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.domains.projects.repository import ProjectRepository
from app.domains.style.repository import StyleRepository
from app.domains.style.schemas import (
    ActiveStyleResponse,
    EpubInspectResponse,
    ReferenceWorkDetailResponse,
    ReferenceWorkListResponse,
    ReferenceWorkResponse,
    StyleAnalysisJobResponse,
    StyleProfileListResponse,
    StyleProfileResponse,
    StyleProfileUpdate,
)
from app.domains.style.service import StyleService

router = APIRouter(tags=["materials"])


def get_style_service(db: Session = Depends(get_db)) -> StyleService:
    return StyleService(db, ProjectRepository(db), StyleRepository(db))


@router.post(
    f"{settings.api_prefix}/materials/references/inspect-epub",
    response_model=EpubInspectResponse,
)
def inspect_epub(
    file: UploadFile = File(...),
    service: StyleService = Depends(get_style_service),
) -> EpubInspectResponse:
    return service.inspect_epub(file)


@router.post(
    f"{settings.api_prefix}/materials/references/upload",
    response_model=ReferenceWorkResponse,
    status_code=201,
)
def upload_library_reference(
    author: str = Form(...),
    title: str | None = Form(default=None),
    file: UploadFile = File(...),
    service: StyleService = Depends(get_style_service),
) -> ReferenceWorkResponse:
    return service.upload_library_reference(author=author, title=title, file=file)


@router.get(
    f"{settings.api_prefix}/materials/references",
    response_model=ReferenceWorkListResponse,
)
def list_library_references(
    service: StyleService = Depends(get_style_service),
) -> ReferenceWorkListResponse:
    return service.list_library_references()


@router.get(
    f"{settings.api_prefix}/materials/references/{{reference_id}}",
    response_model=ReferenceWorkDetailResponse,
)
def get_library_reference(
    reference_id: str,
    service: StyleService = Depends(get_style_service),
) -> ReferenceWorkDetailResponse:
    return service.get_library_reference(reference_id)


@router.post(
    f"{settings.api_prefix}/materials/references/{{reference_id}}/analyze",
    response_model=StyleAnalysisJobResponse,
    status_code=201,
)
def analyze_library_reference(
    reference_id: str,
    service: StyleService = Depends(get_style_service),
) -> StyleAnalysisJobResponse:
    return service.start_library_analysis(reference_id)


@router.get(
    f"{settings.api_prefix}/materials/style-analysis/jobs/{{job_id}}",
    response_model=StyleAnalysisJobResponse,
)
def get_style_analysis_job(
    job_id: str,
    service: StyleService = Depends(get_style_service),
) -> StyleAnalysisJobResponse:
    return service.get_analysis_job(job_id)


@router.get(
    f"{settings.api_prefix}/materials/style-profiles",
    response_model=StyleProfileListResponse,
)
def list_library_style_profiles(
    service: StyleService = Depends(get_style_service),
) -> StyleProfileListResponse:
    return service.list_library_profiles()


@router.get(
    f"{settings.api_prefix}/materials/style-profiles/{{profile_id}}",
    response_model=StyleProfileResponse,
)
def get_library_style_profile(
    profile_id: str,
    service: StyleService = Depends(get_style_service),
) -> StyleProfileResponse:
    return service.get_library_profile(profile_id)


@router.patch(
    f"{settings.api_prefix}/materials/style-profiles/{{profile_id}}",
    response_model=StyleProfileResponse,
)
def update_library_style_profile(
    profile_id: str,
    data: StyleProfileUpdate,
    service: StyleService = Depends(get_style_service),
) -> StyleProfileResponse:
    return service.update_library_profile(profile_id, data)


@router.post(
    f"{settings.api_prefix}/materials/style-profiles/{{profile_id}}/confirm",
    response_model=StyleProfileResponse,
)
def confirm_library_style_profile(
    profile_id: str,
    service: StyleService = Depends(get_style_service),
) -> StyleProfileResponse:
    return service.confirm_library_profile(profile_id)


@router.post(
    f"{settings.api_prefix}/materials/style-profiles/{{profile_id}}/lock",
    response_model=StyleProfileResponse,
)
def lock_library_style_profile(
    profile_id: str,
    service: StyleService = Depends(get_style_service),
) -> StyleProfileResponse:
    return service.lock_library_profile(profile_id)


@router.post(
    f"{settings.api_prefix}/materials/style-profiles/{{profile_id}}/unlock",
    response_model=StyleProfileResponse,
)
def unlock_library_style_profile(
    profile_id: str,
    service: StyleService = Depends(get_style_service),
) -> StyleProfileResponse:
    return service.unlock_library_profile(profile_id)


@router.delete(
    f"{settings.api_prefix}/materials/style-profiles/{{profile_id}}",
    status_code=204,
)
def delete_library_style_profile(
    profile_id: str,
    service: StyleService = Depends(get_style_service),
) -> None:
    service.delete_library_profile(profile_id)


@router.get(
    f"{settings.api_prefix}/materials/style-profiles/{{profile_id}}/export/skill",
)
def export_library_style_skill(
    profile_id: str,
    service: StyleService = Depends(get_style_service),
) -> Response:
    payload, filename = service.export_library_skill(profile_id)
    return Response(
        content=payload,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post(
    f"{settings.api_prefix}/projects/{{project_id}}/materials/style-profiles/{{profile_id}}/bind",
    response_model=ActiveStyleResponse,
)
def bind_style_profile(
    project_id: str,
    profile_id: str,
    service: StyleService = Depends(get_style_service),
) -> ActiveStyleResponse:
    return service.bind_profile(project_id, profile_id)


@router.get(
    f"{settings.api_prefix}/projects/{{project_id}}/materials/active-style",
    response_model=ActiveStyleResponse,
)
def get_active_style(
    project_id: str,
    service: StyleService = Depends(get_style_service),
) -> ActiveStyleResponse:
    return service.get_active_style(project_id)
