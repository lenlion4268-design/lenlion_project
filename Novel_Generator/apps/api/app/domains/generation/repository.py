from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.enums import AssetSourceType, ConfirmStatus, GenerationJobStatus, LockStatus
from app.domains.assets.models import Outline, Volume
from app.domains.assets.schemas import OutlineCreate, VolumeCreate
from app.domains.assets.repository import AssetRepository
from app.domains.generation.models import Chapter, GenerationJob
from app.domains.generation.schemas import ChapterUpdate, OutlineDraft, VolumeDraft


def _touch(entity: object) -> None:
    if hasattr(entity, "updated_at"):
        entity.updated_at = datetime.now(UTC)  # type: ignore[attr-defined]


class GenerationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_job(
        self,
        *,
        project_id: str,
        target_stage: str,
        outline_id: str | None,
        volume_id: str | None,
        provider: str,
        model_profile: str,
        model_name: str | None,
        execution_mode: str,
    ) -> GenerationJob:
        job = GenerationJob(
            project_id=project_id,
            target_stage=target_stage,
            outline_id=outline_id,
            volume_id=volume_id,
            status=GenerationJobStatus.QUEUED,
            provider=provider,
            model_profile=model_profile,
            model_name=model_name,
            execution_mode=execution_mode,
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def update_job(self, job: GenerationJob, **fields: object) -> GenerationJob:
        for key, value in fields.items():
            setattr(job, key, value)
        _touch(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def get_job(self, job_id: str) -> GenerationJob | None:
        return self.db.get(GenerationJob, job_id)

    def list_jobs(self, project_id: str) -> list[GenerationJob]:
        stmt = (
            select(GenerationJob)
            .where(GenerationJob.project_id == project_id)
            .order_by(GenerationJob.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def count_volumes(self, project_id: str) -> int:
        stmt = select(func.count()).select_from(Volume).where(Volume.project_id == project_id)
        return int(self.db.scalar(stmt) or 0)

    def count_chapters(self, volume_id: str) -> int:
        stmt = select(func.count()).select_from(Chapter).where(Chapter.volume_id == volume_id)
        return int(self.db.scalar(stmt) or 0)

    def next_volume_no(self, project_id: str) -> int:
        stmt = select(func.max(Volume.volume_no)).where(Volume.project_id == project_id)
        current = self.db.scalar(stmt)
        return int(current or 0) + 1

    def create_outline_from_draft(self, project_id: str, draft: OutlineDraft) -> Outline:
        repo = AssetRepository(self.db)
        return repo.create_outline(
            project_id,
            OutlineCreate(
                title=draft.title,
                summary=draft.summary,
                plot_nodes_json=draft.plot_nodes_json,
                character_arcs_json=draft.character_arcs_json,
                ending_direction=draft.ending_direction,
            ),
        )

    def create_volume_from_draft(self, project_id: str, draft: VolumeDraft) -> Volume:
        repo = AssetRepository(self.db)
        return repo.create_volume(
            project_id,
            VolumeCreate(
                outline_id=draft.outline_id,
                volume_no=draft.volume_no,
                title=draft.title,
                stage_goal=draft.stage_goal,
                main_conflict=draft.main_conflict,
                key_events_json=draft.key_events_json,
                involved_characters=draft.involved_characters,
                emotional_rhythm=draft.emotional_rhythm,
                previous_relation=draft.previous_relation,
                next_relation=draft.next_relation,
            ),
        )

    def create_chapter(
        self,
        *,
        project_id: str,
        volume_id: str,
        generation_job_id: str,
        chapter_no: int,
        title: str,
        content: str,
    ) -> Chapter:
        chapter = Chapter(
            project_id=project_id,
            volume_id=volume_id,
            generation_job_id=generation_job_id,
            chapter_no=chapter_no,
            title=title,
            content=content,
            word_count=len(content),
            source_type=AssetSourceType.AI_SUGGESTED,
            confirm_status=ConfirmStatus.DRAFT,
        )
        self.db.add(chapter)
        self.db.commit()
        self.db.refresh(chapter)
        return chapter

    def list_chapters(self, project_id: str, volume_id: str | None = None) -> list[Chapter]:
        stmt = select(Chapter).where(Chapter.project_id == project_id)
        if volume_id is not None:
            stmt = stmt.where(Chapter.volume_id == volume_id)
        stmt = stmt.order_by(Chapter.chapter_no.asc(), Chapter.updated_at.desc())
        return list(self.db.scalars(stmt).all())

    def list_manuscript_chapters(
        self,
        project_id: str,
        *,
        volume_id: str | None = None,
        include_drafts: bool = False,
    ) -> list[Chapter]:
        stmt = select(Chapter).where(Chapter.project_id == project_id)
        if volume_id is not None:
            stmt = stmt.where(Chapter.volume_id == volume_id)
        if not include_drafts:
            stmt = stmt.where(
                (Chapter.confirm_status == ConfirmStatus.LOCKED)
                | (Chapter.lock_status == LockStatus.LOCKED)
            )
        stmt = stmt.order_by(Chapter.volume_id.asc(), Chapter.chapter_no.asc())
        return list(self.db.scalars(stmt).all())

    def get_chapter(self, chapter_id: str) -> Chapter | None:
        return self.db.get(Chapter, chapter_id)

    def update_chapter(self, chapter: Chapter, data: ChapterUpdate) -> Chapter:
        updates = data.model_dump(exclude_unset=True)
        if "content" in updates and updates["content"] is not None:
            chapter.word_count = len(updates["content"])
        for key, value in updates.items():
            setattr(chapter, key, value)
        chapter.confirm_status = ConfirmStatus.DRAFT
        _touch(chapter)
        self.db.commit()
        self.db.refresh(chapter)
        return chapter
