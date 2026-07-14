from app.core.errors import ForbiddenError, NotFoundError
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
from app.domains.projects.repository import ProjectRepository


class AssetService:
    def __init__(
        self,
        asset_repo: AssetRepository,
        project_repo: ProjectRepository,
        status_service: AssetStatusService,
    ) -> None:
        self.asset_repo = asset_repo
        self.project_repo = project_repo
        self.status_service = status_service

    def create_character_card(
        self, project_id: str, data: CharacterCardCreate
    ) -> CharacterCardResponse:
        self._require_project(project_id)
        card = self.asset_repo.create_character_card(project_id, data)
        return CharacterCardResponse.model_validate(card)

    def list_character_cards(self, project_id: str) -> CharacterCardListResponse:
        self._require_project(project_id)
        cards = self.asset_repo.list_character_cards(project_id)
        items = [CharacterCardResponse.model_validate(c) for c in cards]
        return CharacterCardListResponse(items=items, total=len(items))

    def update_character_card(self, card_id: str, data: CharacterCardUpdate) -> CharacterCardResponse:
        card = self.asset_repo.get_character_card(card_id)
        if card is None:
            raise NotFoundError("Character card not found")
        self.status_service.ensure_editable(card)
        updated = self.asset_repo.update_character_card(card, data)
        return CharacterCardResponse.model_validate(updated)

    def upsert_theme_profile(
        self, project_id: str, data: ThemeProfileUpsert
    ) -> ThemeProfileResponse:
        self._require_project(project_id)
        profile = self.asset_repo.get_theme_profile(project_id)
        if profile is not None:
            self.status_service.ensure_editable(profile)
        profile = self.asset_repo.upsert_theme_profile(project_id, data)
        return ThemeProfileResponse.model_validate(profile)

    def get_theme_profile(self, project_id: str) -> ThemeProfileResponse:
        self._require_project(project_id)
        profile = self.asset_repo.get_theme_profile(project_id)
        if profile is None:
            raise NotFoundError("Theme profile not found")
        return ThemeProfileResponse.model_validate(profile)

    def upsert_world_setting(
        self, project_id: str, data: WorldSettingUpsert
    ) -> WorldSettingResponse:
        self._require_project(project_id)
        setting = self.asset_repo.get_world_setting(project_id)
        if setting is not None:
            self.status_service.ensure_editable(setting)
        setting = self.asset_repo.upsert_world_setting(project_id, data)
        return WorldSettingResponse.model_validate(setting)

    def get_world_setting(self, project_id: str) -> WorldSettingResponse:
        self._require_project(project_id)
        setting = self.asset_repo.get_world_setting(project_id)
        if setting is None:
            raise NotFoundError("World setting not found")
        return WorldSettingResponse.model_validate(setting)

    def create_outline(self, project_id: str, data: OutlineCreate) -> OutlineResponse:
        self._require_project(project_id)
        outline = self.asset_repo.create_outline(project_id, data)
        return OutlineResponse.model_validate(outline)

    def list_outlines(self, project_id: str) -> OutlineListResponse:
        self._require_project(project_id)
        outlines = self.asset_repo.list_outlines(project_id)
        items = [OutlineResponse.model_validate(o) for o in outlines]
        return OutlineListResponse(items=items, total=len(items))

    def create_volume(self, project_id: str, data: VolumeCreate) -> VolumeResponse:
        self._require_project(project_id)
        volume = self.asset_repo.create_volume(project_id, data)
        return VolumeResponse.model_validate(volume)

    def list_volumes(self, project_id: str) -> VolumeListResponse:
        self._require_project(project_id)
        volumes = self.asset_repo.list_volumes(project_id)
        items = [VolumeResponse.model_validate(v) for v in volumes]
        return VolumeListResponse(items=items, total=len(items))

    def _require_project(self, project_id: str) -> None:
        if self.project_repo.get_by_id(project_id) is None:
            raise NotFoundError("Project not found")
