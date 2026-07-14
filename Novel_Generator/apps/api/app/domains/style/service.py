from datetime import UTC, datetime
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import AssetSourceType, ConfirmStatus, LockStatus, ReferenceWorkStatus, StyleAnalysisJobStatus
from app.core.errors import AppError, ForbiddenError, NotFoundError
from app.domains.assets.models import ThemeProfile
from app.domains.projects.models import NovelProject
from app.domains.assets.status_service import is_locked_asset
from app.domains.projects.repository import ProjectRepository
from app.domains.style.analyzer import get_style_analyzer
from app.domains.style.epub_reader import extract_epub_metadata
from app.domains.style.ingest import (
    ingest_reference,
    mark_reference_ingested,
    normalize_format,
    persist_samples,
)
from app.domains.style.models import ReferenceWork
from app.domains.style.repository import StyleRepository
from app.domains.style.schemas import (
    ActiveStyleResponse,
    EpubInspectResponse,
    ReferenceSampleResponse,
    ReferenceWorkDetailResponse,
    ReferenceWorkListResponse,
    ReferenceWorkResponse,
    StyleAnalysisJobResponse,
    StyleProfileListResponse,
    StyleProfileResponse,
    StyleProfileUpdate,
)
from app.domains.style.skill_exporter import export_skill_zip


class StyleService:
    def __init__(
        self,
        db: Session,
        project_repo: ProjectRepository,
        style_repo: StyleRepository,
    ) -> None:
        self.db = db
        self.project_repo = project_repo
        self.style_repo = style_repo

    def inspect_epub(self, file: UploadFile) -> EpubInspectResponse:
        if not file.filename or not file.filename.lower().endswith(".epub"):
            raise AppError(400, "Only EPUB files can be inspected")
        temp_path = self._save_temp(file)
        try:
            author, title = extract_epub_metadata(temp_path)
            return EpubInspectResponse(suggested_author=author, suggested_title=title)
        finally:
            temp_path.unlink(missing_ok=True)

    def upload_library_reference(
        self,
        *,
        author: str,
        title: str | None,
        file: UploadFile,
    ) -> ReferenceWorkResponse:
        return self._upload_reference(project_id=None, author=author, title=title, file=file)

    def list_library_references(self) -> ReferenceWorkListResponse:
        items = [
            ReferenceWorkResponse.model_validate(item)
            for item in self.style_repo.list_references()
        ]
        return ReferenceWorkListResponse(items=items, total=len(items))

    def get_library_reference(self, reference_id: str) -> ReferenceWorkDetailResponse:
        reference = self._get_library_reference(reference_id)
        samples = self.style_repo.list_samples(reference_id)
        base = ReferenceWorkResponse.model_validate(reference)
        return ReferenceWorkDetailResponse(
            **base.model_dump(),
            samples=[ReferenceSampleResponse.model_validate(item) for item in samples],
        )

    def start_library_analysis(self, reference_id: str) -> StyleAnalysisJobResponse:
        reference = self._get_library_reference(reference_id)
        if reference.status != ReferenceWorkStatus.INGESTED.value:
            self._ingest_reference(reference)
            reference = self.style_repo.get_reference(reference_id)
            assert reference is not None

        job = self.style_repo.create_analysis_job(
            project_id=None,
            reference_work_id=reference_id,
        )
        if settings.style_analysis_force_sync:
            return self.execute_analysis(job.id)

        from app.domains.style.worker import enqueue_style_analysis

        enqueue_style_analysis(job.id)
        refreshed = self.style_repo.get_analysis_job(job.id)
        assert refreshed is not None
        return StyleAnalysisJobResponse.model_validate(refreshed)

    def get_analysis_job(self, job_id: str) -> StyleAnalysisJobResponse:
        job = self.style_repo.get_analysis_job(job_id)
        if job is None:
            raise NotFoundError("Style analysis job not found")
        return StyleAnalysisJobResponse.model_validate(job)

    def execute_analysis(self, job_id: str) -> StyleAnalysisJobResponse:
        job = self.style_repo.get_analysis_job(job_id)
        if job is None:
            raise NotFoundError("Style analysis job not found")
        if job.status in (StyleAnalysisJobStatus.SUCCEEDED, StyleAnalysisJobStatus.FAILED):
            return StyleAnalysisJobResponse.model_validate(job)

        reference = self.style_repo.get_reference(job.reference_work_id)
        if reference is None:
            raise NotFoundError("Reference work not found")

        job = self.style_repo.update_analysis_job(job, status=StyleAnalysisJobStatus.RUNNING)
        try:
            if reference.status != ReferenceWorkStatus.INGESTED.value:
                self._ingest_reference(reference)
                reference = self.style_repo.get_reference(reference.id)
                assert reference is not None

            samples = self.style_repo.list_samples(reference.id)
            result = get_style_analyzer().analyze(reference, samples)
            profile = self.style_repo.create_profile(
                project_id=reference.project_id,
                reference_work_id=reference.id,
                author=reference.author,
                reference_title=reference.title,
                name=str(result["name"]),
                voice_summary=str(result["voice_summary"]),
                profile_json=result["profile_json"],
                skill_markdown=str(result["skill_markdown"]),
            )
            job = self.style_repo.update_analysis_job(
                job,
                status=StyleAnalysisJobStatus.SUCCEEDED,
                style_profile_id=profile.id,
                completed_at=datetime.now(UTC),
            )
        except Exception as exc:  # noqa: BLE001
            job = self.style_repo.update_analysis_job(
                job,
                status=StyleAnalysisJobStatus.FAILED,
                error_message=str(exc),
                completed_at=datetime.now(UTC),
            )
            return StyleAnalysisJobResponse.model_validate(job)
        return StyleAnalysisJobResponse.model_validate(job)

    def list_library_profiles(self) -> StyleProfileListResponse:
        items = [
            StyleProfileResponse.model_validate(item)
            for item in self.style_repo.list_profiles()
        ]
        return StyleProfileListResponse(items=items, total=len(items))

    def get_library_profile(self, profile_id: str) -> StyleProfileResponse:
        profile = self._get_library_profile(profile_id)
        return StyleProfileResponse.model_validate(profile)

    def update_library_profile(self, profile_id: str, data: StyleProfileUpdate) -> StyleProfileResponse:
        profile = self._get_library_profile(profile_id)
        if is_locked_asset(profile):
            raise ForbiddenError("Locked style profile cannot be edited")
        updates = data.model_dump(exclude_unset=True)
        profile = self.style_repo.update_profile(profile, **updates)
        return StyleProfileResponse.model_validate(profile)

    def confirm_library_profile(self, profile_id: str) -> StyleProfileResponse:
        profile = self._get_library_profile(profile_id)
        profile = self.style_repo.update_profile(profile, confirm_status=ConfirmStatus.CONFIRMED)
        return StyleProfileResponse.model_validate(profile)

    def lock_library_profile(self, profile_id: str) -> StyleProfileResponse:
        profile = self._get_library_profile(profile_id)
        profile = self.style_repo.update_profile(
            profile,
            confirm_status=ConfirmStatus.LOCKED,
            lock_status=LockStatus.LOCKED,
        )
        return StyleProfileResponse.model_validate(profile)

    def unlock_library_profile(self, profile_id: str) -> StyleProfileResponse:
        profile = self._get_library_profile(profile_id)
        bound = (
            self.db.query(NovelProject)
            .filter(NovelProject.active_style_profile_id == profile_id)
            .first()
        )
        if bound is not None:
            raise ForbiddenError("Bound style profile cannot be unlocked; unbind from project first")
        profile = self.style_repo.update_profile(
            profile,
            confirm_status=ConfirmStatus.CONFIRMED,
            lock_status=LockStatus.UNLOCKED,
        )
        return StyleProfileResponse.model_validate(profile)

    def delete_library_profile(self, profile_id: str) -> None:
        profile = self._get_library_profile(profile_id)
        if is_locked_asset(profile):
            raise ForbiddenError("Locked style profile cannot be deleted; unlock first")
        bound = (
            self.db.query(NovelProject)
            .filter(NovelProject.active_style_profile_id == profile_id)
            .first()
        )
        if bound is not None:
            raise ForbiddenError("Style profile is bound to a project; unbind first")
        self.style_repo.delete_profile(profile)

    def bind_profile(self, project_id: str, profile_id: str) -> ActiveStyleResponse:
        project = self.project_repo.get_by_id(project_id)
        if project is None:
            raise NotFoundError("Project not found")
        profile = self._get_library_profile(profile_id)
        if not is_locked_asset(profile):
            raise ForbiddenError("Only locked style profiles can be bound")

        project.active_style_profile_id = profile.id
        self.db.commit()
        self.db.refresh(project)

        theme = self.db.query(ThemeProfile).filter_by(project_id=project_id).first()
        if theme is not None:
            theme.narrative_style = profile.voice_summary
            self.db.commit()

        return ActiveStyleResponse(
            active_style_profile_id=profile.id,
            author=profile.author,
            name=profile.name,
        )

    def get_active_style(self, project_id: str) -> ActiveStyleResponse:
        project = self.project_repo.get_by_id(project_id)
        if project is None:
            raise NotFoundError("Project not found")
        if not project.active_style_profile_id:
            return ActiveStyleResponse(active_style_profile_id=None)
        profile = self.style_repo.get_profile(project.active_style_profile_id)
        if profile is None:
            return ActiveStyleResponse(active_style_profile_id=None)
        return ActiveStyleResponse(
            active_style_profile_id=profile.id,
            author=profile.author,
            name=profile.name,
        )

    def export_library_skill(self, profile_id: str) -> tuple[bytes, str]:
        profile = self._get_library_profile(profile_id)
        from app.domains.style.skill_exporter import slugify

        filename = f"style-{slugify(profile.author)}.zip"
        return export_skill_zip(profile), filename

    def _upload_reference(
        self,
        project_id: str | None,
        *,
        author: str,
        title: str | None,
        file: UploadFile,
    ) -> ReferenceWorkResponse:
        if project_id is not None and self.project_repo.get_by_id(project_id) is None:
            raise NotFoundError("Project not found")
        if not author or not author.strip():
            raise AppError(400, "author is required")

        if not file.filename:
            raise AppError(400, "filename is required")
        fmt = normalize_format(file.filename)
        if fmt is None:
            raise AppError(400, "Unsupported file format; use txt, md, or epub")

        content = file.file.read()
        max_bytes = settings.style_upload_max_mb * 1024 * 1024
        if len(content) > max_bytes:
            raise AppError(400, f"File exceeds {settings.style_upload_max_mb}MB limit")

        work_title = (title or Path(file.filename).stem).strip()
        storage_root = (
            Path(settings.local_storage_dir) / project_id / "references"
            if project_id
            else Path(settings.local_storage_dir) / "library" / "references"
        )
        storage_root.mkdir(parents=True, exist_ok=True)

        reference = self.style_repo.create_reference(
            project_id=project_id,
            author=author.strip(),
            title=work_title,
            fmt=fmt,
            storage_path="",
            source_type=AssetSourceType.REFERENCE_PARSE.value,
        )
        file_path = storage_root / f"{reference.id}.{fmt}"
        file_path.write_bytes(content)
        reference = self.style_repo.update_reference(reference, storage_path=str(file_path))

        self._ingest_reference(reference)
        return ReferenceWorkResponse.model_validate(reference)

    def _ingest_reference(self, reference: ReferenceWork) -> None:
        try:
            result = ingest_reference(reference)
            self.style_repo.delete_samples(reference.id)
            persist_samples(self.db, reference.id, result.samples)
            mark_reference_ingested(reference, result.word_count)
            self.style_repo.update_reference(
                reference,
                word_count=result.word_count,
                status=ReferenceWorkStatus.INGESTED.value,
                error_message=None,
            )
        except Exception as exc:  # noqa: BLE001
            self.style_repo.update_reference(
                reference,
                status=ReferenceWorkStatus.FAILED.value,
                error_message=str(exc),
            )
            raise

    def _get_library_reference(self, reference_id: str) -> ReferenceWork:
        reference = self.style_repo.get_reference(reference_id)
        if reference is None:
            raise NotFoundError("Reference work not found")
        return reference

    def _get_library_profile(self, profile_id: str):
        profile = self.style_repo.get_profile(profile_id)
        if profile is None:
            raise NotFoundError("Style profile not found")
        return profile

    def _save_temp(self, file: UploadFile) -> Path:
        temp_dir = Path(settings.local_storage_dir) / "_tmp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_path = temp_dir / (file.filename or "upload.epub")
        temp_path.write_bytes(file.file.read())
        file.file.seek(0)
        return temp_path
