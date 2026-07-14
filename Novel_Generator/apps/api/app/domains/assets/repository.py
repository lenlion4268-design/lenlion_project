from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import ConfirmStatus
from app.domains.assets.models import CharacterCard, Outline, ThemeProfile, Volume, WorldSetting
from app.domains.assets.schemas import (
    CharacterCardCreate,
    CharacterCardUpdate,
    OutlineCreate,
    ThemeProfileUpsert,
    VolumeCreate,
    WorldSettingUpsert,
)


def _touch(entity: object) -> None:
    if hasattr(entity, "updated_at"):
        entity.updated_at = datetime.now(UTC)  # type: ignore[attr-defined]


class AssetRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_character_card(self, project_id: str, data: CharacterCardCreate) -> CharacterCard:
        card = CharacterCard(
            project_id=project_id,
            name=data.name,
            card_type=data.card_type,
            profile_json=data.profile_json.model_dump(),
            tags=data.tags,
            source_type=data.source_type,
            confirm_status=ConfirmStatus.DRAFT,
        )
        self.db.add(card)
        self.db.commit()
        self.db.refresh(card)
        return card

    def list_character_cards(self, project_id: str) -> list[CharacterCard]:
        stmt = (
            select(CharacterCard)
            .where(CharacterCard.project_id == project_id)
            .order_by(CharacterCard.updated_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def get_character_card(self, card_id: str) -> CharacterCard | None:
        return self.db.get(CharacterCard, card_id)

    def update_character_card(self, card: CharacterCard, data: CharacterCardUpdate) -> CharacterCard:
        updates = data.model_dump(exclude_unset=True)
        if "profile_json" in updates and updates["profile_json"] is not None:
            updates["profile_json"] = updates["profile_json"].model_dump()
        for key, value in updates.items():
            setattr(card, key, value)
        card.confirm_status = ConfirmStatus.DRAFT
        _touch(card)
        self.db.commit()
        self.db.refresh(card)
        return card

    def get_theme_profile(self, project_id: str) -> ThemeProfile | None:
        stmt = select(ThemeProfile).where(ThemeProfile.project_id == project_id)
        return self.db.scalars(stmt).first()

    def upsert_theme_profile(self, project_id: str, data: ThemeProfileUpsert) -> ThemeProfile:
        profile = self.get_theme_profile(project_id)
        payload = data.model_dump()
        if profile is None:
            profile = ThemeProfile(project_id=project_id, **payload, confirm_status=ConfirmStatus.DRAFT)
            self.db.add(profile)
        else:
            for key, value in payload.items():
                setattr(profile, key, value)
            profile.confirm_status = ConfirmStatus.DRAFT
            _touch(profile)
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def get_world_setting(self, project_id: str) -> WorldSetting | None:
        stmt = select(WorldSetting).where(WorldSetting.project_id == project_id)
        return self.db.scalars(stmt).first()

    def upsert_world_setting(self, project_id: str, data: WorldSettingUpsert) -> WorldSetting:
        setting = self.get_world_setting(project_id)
        background = data.background_json.model_dump()
        if setting is None:
            setting = WorldSetting(
                project_id=project_id,
                background_json=background,
                confirm_status=ConfirmStatus.DRAFT,
            )
            self.db.add(setting)
        else:
            setting.background_json = background
            setting.confirm_status = ConfirmStatus.DRAFT
            _touch(setting)
        self.db.commit()
        self.db.refresh(setting)
        return setting

    def create_outline(self, project_id: str, data: OutlineCreate) -> Outline:
        outline = Outline(
            project_id=project_id,
            title=data.title,
            summary=data.summary,
            plot_nodes_json=data.plot_nodes_json,
            character_arcs_json=data.character_arcs_json,
            ending_direction=data.ending_direction,
            confirm_status=ConfirmStatus.DRAFT,
        )
        self.db.add(outline)
        self.db.commit()
        self.db.refresh(outline)
        return outline

    def list_outlines(self, project_id: str) -> list[Outline]:
        stmt = (
            select(Outline)
            .where(Outline.project_id == project_id)
            .order_by(Outline.updated_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def create_volume(self, project_id: str, data: VolumeCreate) -> Volume:
        volume = Volume(
            project_id=project_id,
            outline_id=data.outline_id,
            volume_no=data.volume_no,
            title=data.title,
            stage_goal=data.stage_goal,
            main_conflict=data.main_conflict,
            key_events_json=data.key_events_json,
            involved_characters=data.involved_characters,
            emotional_rhythm=data.emotional_rhythm,
            previous_relation=data.previous_relation,
            next_relation=data.next_relation,
            confirm_status=ConfirmStatus.DRAFT,
        )
        self.db.add(volume)
        self.db.commit()
        self.db.refresh(volume)
        return volume

    def list_volumes(self, project_id: str) -> list[Volume]:
        stmt = (
            select(Volume)
            .where(Volume.project_id == project_id)
            .order_by(Volume.volume_no.asc(), Volume.updated_at.desc())
        )
        return list(self.db.scalars(stmt).all())
