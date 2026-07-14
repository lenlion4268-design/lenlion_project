from sqlalchemy.orm import Session

from app.core.enums import ConfirmStatus, LockStatus, ReadinessStage, ReviewAction, ReviewTargetType
from app.core.errors import ConflictError, NotFoundError
from app.domains.assets.models import CharacterCard, Outline, ThemeProfile, Volume, WorldSetting
from app.domains.assets.status_service import AssetStatusService, is_confirmed_or_better, is_locked_asset
from app.domains.projects.repository import ProjectRepository
from app.domains.review.models import ReviewRecord
from app.domains.review.schemas import (
    ReadinessMissingItem,
    ReadinessResponse,
    ReviewRequest,
    ReviewResponse,
)


class ReviewService:
    def __init__(
        self,
        db: Session,
        project_repo: ProjectRepository,
        status_service: AssetStatusService,
    ) -> None:
        self.db = db
        self.project_repo = project_repo
        self.status_service = status_service

    def confirm(self, data: ReviewRequest) -> ReviewResponse:
        return self._apply_action(data, ReviewAction.CONFIRM)

    def lock(self, data: ReviewRequest) -> ReviewResponse:
        return self._apply_action(data, ReviewAction.LOCK)

    def reject(self, data: ReviewRequest) -> ReviewResponse:
        return self._apply_action(data, ReviewAction.REJECT)

    def unlock(self, data: ReviewRequest) -> ReviewResponse:
        return self._apply_action(data, ReviewAction.UNLOCK)

    def _apply_action(self, data: ReviewRequest, action: ReviewAction) -> ReviewResponse:
        located = self.status_service.locate(data.target_type, data.target_id)
        asset = located.asset
        if self.project_repo.get_by_id(asset.project_id) is None:
            raise NotFoundError("Project not found")

        before_status = asset.confirm_status
        after_status = self._next_status(before_status, action)

        asset.confirm_status = after_status
        if action == ReviewAction.LOCK:
            asset.lock_status = LockStatus.LOCKED
        elif action == ReviewAction.UNLOCK:
            asset.lock_status = LockStatus.UNLOCKED

        record = ReviewRecord(
            project_id=asset.project_id,
            target_type=data.target_type,
            target_id=data.target_id,
            action=action,
            operator_id=data.operator_id,
            comment=data.comment,
            before_status=before_status,
            after_status=after_status,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(asset)
        self.db.refresh(record)

        return ReviewResponse(
            target_type=data.target_type,
            target_id=data.target_id,
            confirm_status=after_status,
            lock_status=asset.lock_status,
            action=action,
            review_record_id=record.id,
        )

    def _next_status(self, current: str, action: ReviewAction) -> ConfirmStatus:
        if action == ReviewAction.CONFIRM:
            if current in (ConfirmStatus.DRAFT, ConfirmStatus.PENDING_CONFIRM, ConfirmStatus.REJECTED):
                return ConfirmStatus.CONFIRMED
            raise ConflictError(f"Cannot confirm asset in status '{current}'")

        if action == ReviewAction.LOCK:
            if current in (ConfirmStatus.CONFIRMED, ConfirmStatus.DRAFT, ConfirmStatus.PENDING_CONFIRM):
                return ConfirmStatus.LOCKED
            raise ConflictError(f"Cannot lock asset in status '{current}'")

        if action == ReviewAction.REJECT:
            if current in (
                ConfirmStatus.DRAFT,
                ConfirmStatus.PENDING_CONFIRM,
                ConfirmStatus.CONFIRMED,
            ):
                return ConfirmStatus.REJECTED
            raise ConflictError(f"Cannot reject asset in status '{current}'")

        if action == ReviewAction.UNLOCK:
            if current == ConfirmStatus.LOCKED:
                return ConfirmStatus.CONFIRMED
            raise ConflictError(f"Cannot unlock asset in status '{current}'")

        raise ConflictError("Unsupported review action")


class ReadinessService:
    def __init__(self, db: Session, project_repo: ProjectRepository) -> None:
        self.db = db
        self.project_repo = project_repo

    def check(
        self,
        project_id: str,
        target_stage: ReadinessStage,
        *,
        outline_id: str | None = None,
        volume_id: str | None = None,
    ) -> ReadinessResponse:
        if self.project_repo.get_by_id(project_id) is None:
            raise NotFoundError("Project not found")

        missing: list[ReadinessMissingItem] = []
        blocked: list[str] = []

        if target_stage == ReadinessStage.OUTLINE:
            self._check_outline_prerequisites(project_id, missing, blocked)
        elif target_stage == ReadinessStage.VOLUMES:
            self._check_volume_prerequisites(project_id, outline_id, missing, blocked)
        elif target_stage == ReadinessStage.CHAPTERS:
            self._check_chapter_prerequisites(project_id, volume_id, missing, blocked)

        return ReadinessResponse(
            project_id=project_id,
            target_stage=target_stage,
            ready=len(missing) == 0,
            missing_items=missing,
            blocked_reasons=blocked,
        )

    def _check_outline_prerequisites(
        self,
        project_id: str,
        missing: list[ReadinessMissingItem],
        blocked: list[str],
    ) -> None:
        theme = self.db.query(ThemeProfile).filter_by(project_id=project_id).first()
        if theme is None or not is_confirmed_or_better(theme.confirm_status):
            missing.append(
                ReadinessMissingItem(
                    target_type=ReviewTargetType.THEME_PROFILE,
                    target_id=theme.id if theme else None,
                    label="主题题材",
                    reason="需要已确认或已锁定",
                )
            )
            blocked.append("主题题材尚未确认")

        world = self.db.query(WorldSetting).filter_by(project_id=project_id).first()
        if world is None or not is_confirmed_or_better(world.confirm_status):
            missing.append(
                ReadinessMissingItem(
                    target_type=ReviewTargetType.WORLD_SETTING,
                    target_id=world.id if world else None,
                    label="世界观",
                    reason="需要已确认或已锁定",
                )
            )
            blocked.append("世界观尚未确认")

        characters = (
            self.db.query(CharacterCard)
            .filter(CharacterCard.project_id == project_id)
            .all()
        )
        core_ready = any(is_confirmed_or_better(card.confirm_status) for card in characters)
        if not core_ready:
            missing.append(
                ReadinessMissingItem(
                    target_type=ReviewTargetType.CHARACTER_CARD,
                    label="核心角色",
                    reason="至少需要一个已确认或已锁定的角色卡",
                )
            )
            blocked.append("缺少已确认的核心角色")

    def _check_volume_prerequisites(
        self,
        project_id: str,
        outline_id: str | None,
        missing: list[ReadinessMissingItem],
        blocked: list[str],
    ) -> None:
        if outline_id:
            outline = self.db.get(Outline, outline_id)
            if outline is None or outline.project_id != project_id:
                raise NotFoundError("Outline not found")
            if not is_locked_asset(outline):
                missing.append(
                    ReadinessMissingItem(
                        target_type=ReviewTargetType.OUTLINE,
                        target_id=outline.id,
                        label="大纲",
                        reason="需要已锁定",
                    )
                )
                blocked.append("目标大纲尚未锁定")
            return

        outlines = self.db.query(Outline).filter_by(project_id=project_id).all()
        if not any(is_locked_asset(outline) for outline in outlines):
            missing.append(
                ReadinessMissingItem(
                    target_type=ReviewTargetType.OUTLINE,
                    label="大纲",
                    reason="需要至少一份已锁定的大纲",
                )
            )
            blocked.append("没有已锁定的大纲")

    def _check_chapter_prerequisites(
        self,
        project_id: str,
        volume_id: str | None,
        missing: list[ReadinessMissingItem],
        blocked: list[str],
    ) -> None:
        theme = self.db.query(ThemeProfile).filter_by(project_id=project_id).first()
        if theme is None or not is_locked_asset(theme):
            missing.append(
                ReadinessMissingItem(
                    target_type=ReviewTargetType.THEME_PROFILE,
                    target_id=theme.id if theme else None,
                    label="主题题材",
                    reason="需要已锁定",
                )
            )
            blocked.append("主题题材尚未锁定")

        world = self.db.query(WorldSetting).filter_by(project_id=project_id).first()
        if world is None or not is_locked_asset(world):
            missing.append(
                ReadinessMissingItem(
                    target_type=ReviewTargetType.WORLD_SETTING,
                    target_id=world.id if world else None,
                    label="世界观",
                    reason="需要已锁定",
                )
            )
            blocked.append("世界观尚未锁定")

        outlines = self.db.query(Outline).filter_by(project_id=project_id).all()
        locked_outline = next((item for item in outlines if is_locked_asset(item)), None)
        if locked_outline is None:
            missing.append(
                ReadinessMissingItem(
                    target_type=ReviewTargetType.OUTLINE,
                    label="大纲",
                    reason="需要已锁定",
                )
            )
            blocked.append("大纲尚未锁定")

        if volume_id is None:
            missing.append(
                ReadinessMissingItem(
                    target_type=ReviewTargetType.VOLUME,
                    label="目标故事卷",
                    reason="需要指定 volume_id",
                )
            )
            blocked.append("未指定目标故事卷")
            return

        volume = self.db.get(Volume, volume_id)
        if volume is None or volume.project_id != project_id:
            raise NotFoundError("Volume not found")
        if not is_locked_asset(volume):
            missing.append(
                ReadinessMissingItem(
                    target_type=ReviewTargetType.VOLUME,
                    target_id=volume.id,
                    label="目标故事卷",
                    reason="需要已锁定",
                )
            )
            blocked.append("目标故事卷尚未锁定")

        if volume.involved_characters:
            cards = (
                self.db.query(CharacterCard)
                .filter(CharacterCard.project_id == project_id)
                .filter(CharacterCard.name.in_(volume.involved_characters))
                .all()
            )
            card_by_name = {card.name: card for card in cards}
            for name in volume.involved_characters:
                card = card_by_name.get(name)
                if card is None or not is_confirmed_or_better(card.confirm_status):
                    missing.append(
                        ReadinessMissingItem(
                            target_type=ReviewTargetType.CHARACTER_CARD,
                            target_id=card.id if card else None,
                            label=f"角色：{name}",
                            reason="需要至少已确认",
                        )
                    )
                    blocked.append(f"相关角色「{name}」尚未确认")
