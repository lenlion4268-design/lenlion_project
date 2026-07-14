from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.domains.settings.schemas import (
    EffectiveModelsResponse,
    ModelSettingsUpdate,
    ModelTestResponse,
    PersonalSettingsUpdate,
    SettingsResponse,
)
from app.domains.settings.service import SettingsService

router = APIRouter(tags=["settings"])


def get_settings_service(db: Session = Depends(get_db)) -> SettingsService:
    return SettingsService(db)


@router.get(f"{settings.api_prefix}/settings", response_model=SettingsResponse)
def get_workspace_settings(
    service: SettingsService = Depends(get_settings_service),
) -> SettingsResponse:
    return service.get_settings()


@router.patch(f"{settings.api_prefix}/settings/personal", response_model=SettingsResponse)
def patch_personal_settings(
    data: PersonalSettingsUpdate,
    service: SettingsService = Depends(get_settings_service),
) -> SettingsResponse:
    return service.patch_personal(data)


@router.patch(f"{settings.api_prefix}/settings/models", response_model=SettingsResponse)
def patch_model_settings(
    data: ModelSettingsUpdate,
    service: SettingsService = Depends(get_settings_service),
) -> SettingsResponse:
    return service.patch_models(data)


@router.post(f"{settings.api_prefix}/settings/models/test", response_model=ModelTestResponse)
def test_model_connection(
    service: SettingsService = Depends(get_settings_service),
) -> ModelTestResponse:
    return service.test_connection()


@router.get(
    f"{settings.api_prefix}/settings/models/effective",
    response_model=EffectiveModelsResponse,
)
def get_effective_models(
    service: SettingsService = Depends(get_settings_service),
) -> EffectiveModelsResponse:
    return service.effective_models()
