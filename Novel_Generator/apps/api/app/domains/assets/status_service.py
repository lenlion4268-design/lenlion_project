from dataclasses import dataclass
from typing import Protocol

from sqlalchemy.orm import Session

from app.core.enums import ConfirmStatus, LockStatus, ReviewTargetType
from app.core.errors import ForbiddenError, NotFoundError
from app.domains.assets.models import CharacterCard, Outline, ThemeProfile, Volume, WorldSetting
from app.domains.generation.models import Chapter


class ReviewableAsset(Protocol):
    id: str
    project_id: str
    confirm_status: str
    lock_status: str


@dataclass
class LocatedAsset:
    target_type: ReviewTargetType
    asset: ReviewableAsset


def is_confirmed_or_better(status: str) -> bool:
    return status in (ConfirmStatus.CONFIRMED, ConfirmStatus.LOCKED)


def is_locked_asset(asset: ReviewableAsset) -> bool:
    return (
        asset.confirm_status == ConfirmStatus.LOCKED
        or asset.lock_status == LockStatus.LOCKED
    )


class AssetStatusService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def locate(self, target_type: ReviewTargetType, target_id: str) -> LocatedAsset:
        asset = self._get_asset(target_type, target_id)
        if asset is None:
            raise NotFoundError("Review target not found")
        return LocatedAsset(target_type=target_type, asset=asset)

    def ensure_editable(self, asset: ReviewableAsset) -> None:
        if is_locked_asset(asset):
            raise ForbiddenError("Locked asset cannot be edited")

    def _get_asset(
        self, target_type: ReviewTargetType, target_id: str
    ) -> ReviewableAsset | None:
        if target_type == ReviewTargetType.CHARACTER_CARD:
            return self.db.get(CharacterCard, target_id)
        if target_type == ReviewTargetType.THEME_PROFILE:
            return self.db.get(ThemeProfile, target_id)
        if target_type == ReviewTargetType.WORLD_SETTING:
            return self.db.get(WorldSetting, target_id)
        if target_type == ReviewTargetType.OUTLINE:
            return self.db.get(Outline, target_id)
        if target_type == ReviewTargetType.VOLUME:
            return self.db.get(Volume, target_id)
        if target_type == ReviewTargetType.CHAPTER:
            return self.db.get(Chapter, target_id)
        return None
