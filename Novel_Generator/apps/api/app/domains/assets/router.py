from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.domains.assets.repository import AssetRepository
from app.domains.assets.status_service import AssetStatusService
from app.domains.assets.schemas import (
    CharacterCardCreate,
    CharacterCardListResponse,
    CharacterCardResponse,
    CharacterCardUpdate,
    OutlineCreate,
    OutlineListResponse,
    OutlineResponse,
    ThemeProfileResponse,
    ThemeProfileUpsert,
    VolumeCreate,
    VolumeListResponse,
    VolumeResponse,
    WorldSettingResponse,
    WorldSettingUpsert,
)
from app.domains.assets.service import AssetService
from app.domains.projects.repository import ProjectRepository

router = APIRouter(tags=["assets"])


def get_asset_service(db: Session = Depends(get_db)) -> AssetService:
    return AssetService(AssetRepository(db), ProjectRepository(db), AssetStatusService(db))


@router.post(
    f"{settings.api_prefix}/projects/{{project_id}}/character-cards",
    response_model=CharacterCardResponse,
    status_code=201,
)
def create_character_card(
    project_id: str,
    data: CharacterCardCreate,
    service: AssetService = Depends(get_asset_service),
) -> CharacterCardResponse:
    return service.create_character_card(project_id, data)


@router.get(
    f"{settings.api_prefix}/projects/{{project_id}}/character-cards",
    response_model=CharacterCardListResponse,
)
def list_character_cards(
    project_id: str,
    service: AssetService = Depends(get_asset_service),
) -> CharacterCardListResponse:
    return service.list_character_cards(project_id)


@router.patch(
    f"{settings.api_prefix}/character-cards/{{card_id}}",
    response_model=CharacterCardResponse,
)
def update_character_card(
    card_id: str,
    data: CharacterCardUpdate,
    service: AssetService = Depends(get_asset_service),
) -> CharacterCardResponse:
    return service.update_character_card(card_id, data)


@router.put(
    f"{settings.api_prefix}/projects/{{project_id}}/theme-profile",
    response_model=ThemeProfileResponse,
)
def upsert_theme_profile(
    project_id: str,
    data: ThemeProfileUpsert,
    service: AssetService = Depends(get_asset_service),
) -> ThemeProfileResponse:
    return service.upsert_theme_profile(project_id, data)


@router.get(
    f"{settings.api_prefix}/projects/{{project_id}}/theme-profile",
    response_model=ThemeProfileResponse,
)
def get_theme_profile(
    project_id: str,
    service: AssetService = Depends(get_asset_service),
) -> ThemeProfileResponse:
    return service.get_theme_profile(project_id)


@router.put(
    f"{settings.api_prefix}/projects/{{project_id}}/world-setting",
    response_model=WorldSettingResponse,
)
def upsert_world_setting(
    project_id: str,
    data: WorldSettingUpsert,
    service: AssetService = Depends(get_asset_service),
) -> WorldSettingResponse:
    return service.upsert_world_setting(project_id, data)


@router.get(
    f"{settings.api_prefix}/projects/{{project_id}}/world-setting",
    response_model=WorldSettingResponse,
)
def get_world_setting(
    project_id: str,
    service: AssetService = Depends(get_asset_service),
) -> WorldSettingResponse:
    return service.get_world_setting(project_id)


@router.post(
    f"{settings.api_prefix}/projects/{{project_id}}/outlines",
    response_model=OutlineResponse,
    status_code=201,
)
def create_outline(
    project_id: str,
    data: OutlineCreate,
    service: AssetService = Depends(get_asset_service),
) -> OutlineResponse:
    return service.create_outline(project_id, data)


@router.get(
    f"{settings.api_prefix}/projects/{{project_id}}/outlines",
    response_model=OutlineListResponse,
)
def list_outlines(
    project_id: str,
    service: AssetService = Depends(get_asset_service),
) -> OutlineListResponse:
    return service.list_outlines(project_id)


@router.post(
    f"{settings.api_prefix}/projects/{{project_id}}/volumes",
    response_model=VolumeResponse,
    status_code=201,
)
def create_volume(
    project_id: str,
    data: VolumeCreate,
    service: AssetService = Depends(get_asset_service),
) -> VolumeResponse:
    return service.create_volume(project_id, data)


@router.get(
    f"{settings.api_prefix}/projects/{{project_id}}/volumes",
    response_model=VolumeListResponse,
)
def list_volumes(
    project_id: str,
    service: AssetService = Depends(get_asset_service),
) -> VolumeListResponse:
    return service.list_volumes(project_id)
