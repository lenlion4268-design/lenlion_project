from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import (
    ConfirmStatus,
    ExecutionMode,
    GenerationJobStatus,
    ModelProfile,
    ReadinessStage,
    ReviewTargetType,
)
from app.core.errors import ForbiddenError, NotFoundError
from app.domains.assets.models import CharacterCard, Outline, ThemeProfile, Volume, WorldSetting
from app.domains.assets.status_service import AssetStatusService, is_confirmed_or_better, is_locked_asset
from app.domains.generation.ai_provider import get_ai_provider
from app.domains.generation.context import GenerationContext
from app.domains.generation.model_router import resolve_model_name
from app.domains.generation.repository import GenerationRepository
from app.domains.generation.schemas import (
    ChapterListResponse,
    ChapterResponse,
    ChapterUpdate,
    GenerationJobListResponse,
    GenerationJobResponse,
    GenerationRequest,
    GenerationRunResponse,
)
from app.domains.generation.worker import enqueue_generation_job
from app.domains.projects.repository import ProjectRepository
from app.domains.review.service import ReadinessService
from app.domains.settings.effective import get_effective_settings
from app.domains.style.models import StyleProfile


class GenerationService:
    def __init__(
        self,
        db: Session,
        project_repo: ProjectRepository,
        generation_repo: GenerationRepository,
        readiness_service: ReadinessService,
        status_service: AssetStatusService,
    ) -> None:
        self.db = db
        self.project_repo = project_repo
        self.generation_repo = generation_repo
        self.readiness_service = readiness_service
        self.status_service = status_service

    def run_generation(self, project_id: str, data: GenerationRequest) -> GenerationRunResponse:
        if self.project_repo.get_by_id(project_id) is None:
            raise NotFoundError("Project not found")

        batch_count = data.batch_count
        if batch_count > 1 and data.target_stage != ReadinessStage.CHAPTERS:
            raise ForbiddenError("batch_count is only supported for chapter generation")
        effective = get_effective_settings()
        if batch_count > effective.ai_batch_max_chapters:
            raise ForbiddenError(
                f"batch_count cannot exceed {effective.ai_batch_max_chapters}"
            )

        execution_mode = ExecutionMode.ASYNC if data.async_mode else ExecutionMode.SYNC
        model_name = resolve_model_name(data.target_stage, data.model_profile)
        jobs: list[GenerationJobResponse] = []

        for _ in range(batch_count):
            job = self._create_pending_job(
                project_id,
                data,
                execution_mode=execution_mode,
                model_profile=data.model_profile,
                model_name=model_name,
            )
            if execution_mode == ExecutionMode.ASYNC:
                if settings.generation_force_sync:
                    jobs.append(self.execute_job(job.id))
                else:
                    enqueue_generation_job(job.id)
                    refreshed = self.generation_repo.get_job(job.id)
                    assert refreshed is not None
                    jobs.append(GenerationJobResponse.model_validate(refreshed))
            else:
                jobs.append(self.execute_job(job.id))

        return GenerationRunResponse(jobs=jobs, total=len(jobs))

    def execute_job(self, job_id: str) -> GenerationJobResponse:
        job = self.generation_repo.get_job(job_id)
        if job is None:
            raise NotFoundError("Generation job not found")
        if job.status in (
            GenerationJobStatus.SUCCEEDED,
            GenerationJobStatus.FAILED,
            GenerationJobStatus.CANCELLED,
        ):
            return GenerationJobResponse.model_validate(job)

        data = GenerationRequest(
            target_stage=ReadinessStage(job.target_stage),
            outline_id=job.outline_id,
            volume_id=job.volume_id,
            model_profile=ModelProfile(job.model_profile),
        )

        readiness = self.readiness_service.check(
            job.project_id,
            data.target_stage,
            outline_id=data.outline_id,
            volume_id=data.volume_id,
        )
        if not readiness.ready:
            job = self.generation_repo.update_job(
                job,
                status=GenerationJobStatus.FAILED,
                error_message="Generation prerequisites not met: "
                + "; ".join(readiness.blocked_reasons),
                completed_at=datetime.now(UTC),
            )
            raise ForbiddenError(job.error_message or "Generation prerequisites not met")

        model_name = job.model_name or resolve_model_name(data.target_stage, data.model_profile)
        effective = get_effective_settings()
        provider = get_ai_provider(effective.ai_provider, model=model_name)
        job = self.generation_repo.update_job(
            job,
            status=GenerationJobStatus.RUNNING,
            model_name=model_name,
        )

        try:
            ctx = self._build_context(job.project_id, data)
            if data.target_stage == ReadinessStage.OUTLINE:
                draft = provider.generate_outline(ctx)
                outline = self.generation_repo.create_outline_from_draft(job.project_id, draft)
                job = self._complete_job(job, ReviewTargetType.OUTLINE, outline.id)
            elif data.target_stage == ReadinessStage.VOLUMES:
                ctx.existing_chapter_count = self.generation_repo.next_volume_no(job.project_id) - 1
                draft = provider.generate_volume(ctx)
                draft.volume_no = self.generation_repo.next_volume_no(job.project_id)
                volume = self.generation_repo.create_volume_from_draft(job.project_id, draft)
                job = self._complete_job(job, ReviewTargetType.VOLUME, volume.id)
            elif data.target_stage == ReadinessStage.CHAPTERS:
                if data.volume_id is None:
                    raise ForbiddenError("volume_id is required for chapter generation")
                ctx.existing_chapter_count = self.generation_repo.count_chapters(data.volume_id)
                draft = provider.generate_chapter(ctx)
                chapter = self.generation_repo.create_chapter(
                    project_id=job.project_id,
                    volume_id=data.volume_id,
                    generation_job_id=job.id,
                    chapter_no=draft.chapter_no,
                    title=draft.title,
                    content=draft.content,
                )
                job = self._complete_job(job, ReviewTargetType.CHAPTER, chapter.id)
            else:
                raise ForbiddenError(f"Unsupported generation stage: {data.target_stage}")
        except Exception as exc:  # noqa: BLE001 — persist failure on job record
            job = self.generation_repo.update_job(
                job,
                status=GenerationJobStatus.FAILED,
                error_message=str(exc),
                completed_at=datetime.now(UTC),
            )
            raise

        return GenerationJobResponse.model_validate(job)

    def _create_pending_job(
        self,
        project_id: str,
        data: GenerationRequest,
        *,
        execution_mode: ExecutionMode,
        model_profile: ModelProfile,
        model_name: str,
    ):
        readiness = self.readiness_service.check(
            project_id,
            data.target_stage,
            outline_id=data.outline_id,
            volume_id=data.volume_id,
        )
        if not readiness.ready:
            raise ForbiddenError(
                "Generation prerequisites not met: " + "; ".join(readiness.blocked_reasons)
            )

        return self.generation_repo.create_job(
            project_id=project_id,
            target_stage=data.target_stage,
            outline_id=data.outline_id,
            volume_id=data.volume_id,
            provider=get_effective_settings().ai_provider,
            model_profile=model_profile,
            model_name=model_name,
            execution_mode=execution_mode,
        )

    def get_job(self, job_id: str) -> GenerationJobResponse:
        job = self.generation_repo.get_job(job_id)
        if job is None:
            raise NotFoundError("Generation job not found")
        return GenerationJobResponse.model_validate(job)

    def cancel_job(self, job_id: str) -> GenerationJobResponse:
        job = self.generation_repo.get_job(job_id)
        if job is None:
            raise NotFoundError("Generation job not found")
        if job.status != GenerationJobStatus.QUEUED:
            raise ForbiddenError("Only queued jobs can be cancelled")
        if job.queue_task_id:
            from app.core.enums import QueueBackend
            from app.domains.generation.queue import resolve_queue_backend
            from app.domains.generation.worker import revoke_generation_job

            if resolve_queue_backend() == QueueBackend.CELERY:
                revoke_generation_job(job.queue_task_id)
        job = self.generation_repo.update_job(
            job,
            status=GenerationJobStatus.CANCELLED,
            completed_at=datetime.now(UTC),
        )
        return GenerationJobResponse.model_validate(job)

    def list_jobs(self, project_id: str) -> GenerationJobListResponse:
        if self.project_repo.get_by_id(project_id) is None:
            raise NotFoundError("Project not found")
        items = [
            GenerationJobResponse.model_validate(job)
            for job in self.generation_repo.list_jobs(project_id)
        ]
        return GenerationJobListResponse(items=items, total=len(items))

    def list_chapters(self, project_id: str, volume_id: str | None = None) -> ChapterListResponse:
        if self.project_repo.get_by_id(project_id) is None:
            raise NotFoundError("Project not found")
        items = [
            ChapterResponse.model_validate(chapter)
            for chapter in self.generation_repo.list_chapters(project_id, volume_id=volume_id)
        ]
        return ChapterListResponse(items=items, total=len(items))

    def get_chapter(self, chapter_id: str) -> ChapterResponse:
        chapter = self.generation_repo.get_chapter(chapter_id)
        if chapter is None:
            raise NotFoundError("Chapter not found")
        return ChapterResponse.model_validate(chapter)

    def update_chapter(self, chapter_id: str, data: ChapterUpdate) -> ChapterResponse:
        chapter = self.generation_repo.get_chapter(chapter_id)
        if chapter is None:
            raise NotFoundError("Chapter not found")
        self.status_service.ensure_editable(chapter)
        updated = self.generation_repo.update_chapter(chapter, data)
        return ChapterResponse.model_validate(updated)

    def _complete_job(self, job, result_type: ReviewTargetType, result_id: str):
        return self.generation_repo.update_job(
            job,
            status=GenerationJobStatus.SUCCEEDED,
            result_type=result_type,
            result_id=result_id,
            completed_at=datetime.now(UTC),
        )

    def _build_context(self, project_id: str, data: GenerationRequest) -> GenerationContext:
        project = self.project_repo.get_by_id(project_id)
        assert project is not None

        theme = self.db.query(ThemeProfile).filter_by(project_id=project_id).first()
        world = self.db.query(WorldSetting).filter_by(project_id=project_id).first()
        characters = (
            self.db.query(CharacterCard)
            .filter(CharacterCard.project_id == project_id)
            .filter(CharacterCard.confirm_status.in_([ConfirmStatus.CONFIRMED, ConfirmStatus.LOCKED]))
            .all()
        )
        if not characters:
            characters = [
                card
                for card in self.db.query(CharacterCard).filter_by(project_id=project_id).all()
                if is_confirmed_or_better(card.confirm_status)
            ]

        outline: Outline | None = None
        if data.outline_id:
            outline = self.db.get(Outline, data.outline_id)
        else:
            outlines = self.db.query(Outline).filter_by(project_id=project_id).all()
            outline = next((item for item in outlines if is_locked_asset(item)), None)

        volume: Volume | None = None
        if data.volume_id:
            volume = self.db.get(Volume, data.volume_id)

        style_profile: StyleProfile | None = None
        if project.active_style_profile_id:
            candidate = self.db.get(StyleProfile, project.active_style_profile_id)
            if candidate is not None and is_locked_asset(candidate):
                style_profile = candidate

        return GenerationContext(
            project=project,
            theme=theme,
            world=world,
            characters=characters,
            outline=outline,
            volume=volume,
            style_profile=style_profile,
        )
