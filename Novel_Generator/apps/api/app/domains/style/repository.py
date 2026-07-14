from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import ConfirmStatus, LockStatus, ReferenceWorkStatus, StyleAnalysisJobStatus
from app.domains.style.models import ReferenceSample, ReferenceWork, StyleAnalysisJob, StyleProfile


def _touch(entity: object) -> None:
    if hasattr(entity, "updated_at"):
        entity.updated_at = datetime.now(UTC)  # type: ignore[attr-defined]


class StyleRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_reference(
        self,
        *,
        project_id: str | None,
        author: str,
        title: str,
        fmt: str,
        storage_path: str,
        source_type: str | None = None,
    ) -> ReferenceWork:
        reference = ReferenceWork(
            project_id=project_id,
            author=author.strip(),
            title=title.strip(),
            format=fmt,
            storage_path=storage_path,
            status=ReferenceWorkStatus.UPLOADED,
        )
        if source_type is not None:
            reference.source_type = source_type
        self.db.add(reference)
        self.db.commit()
        self.db.refresh(reference)
        return reference

    def get_reference(self, reference_id: str) -> ReferenceWork | None:
        return self.db.get(ReferenceWork, reference_id)

    def list_references(self, project_id: str | None = None) -> list[ReferenceWork]:
        stmt = select(ReferenceWork)
        if project_id is not None:
            stmt = stmt.where(ReferenceWork.project_id == project_id)
        stmt = stmt.order_by(ReferenceWork.created_at.desc(), ReferenceWork.author.asc())
        return list(self.db.scalars(stmt).all())

    def update_reference(self, reference: ReferenceWork, **fields: object) -> ReferenceWork:
        for key, value in fields.items():
            setattr(reference, key, value)
        _touch(reference)
        self.db.commit()
        self.db.refresh(reference)
        return reference

    def list_samples(self, reference_id: str) -> list[ReferenceSample]:
        stmt = select(ReferenceSample).where(ReferenceSample.reference_work_id == reference_id)
        return list(self.db.scalars(stmt).all())

    def delete_samples(self, reference_id: str) -> None:
        for sample in self.list_samples(reference_id):
            self.db.delete(sample)
        self.db.commit()

    def create_analysis_job(
        self,
        *,
        project_id: str | None,
        reference_work_id: str,
    ) -> StyleAnalysisJob:
        job = StyleAnalysisJob(
            project_id=project_id,
            reference_work_id=reference_work_id,
            status=StyleAnalysisJobStatus.QUEUED,
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def get_analysis_job(self, job_id: str) -> StyleAnalysisJob | None:
        return self.db.get(StyleAnalysisJob, job_id)

    def update_analysis_job(self, job: StyleAnalysisJob, **fields: object) -> StyleAnalysisJob:
        for key, value in fields.items():
            setattr(job, key, value)
        _touch(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def create_profile(
        self,
        *,
        project_id: str | None,
        reference_work_id: str,
        author: str,
        reference_title: str,
        name: str,
        voice_summary: str,
        profile_json: dict,
        skill_markdown: str,
    ) -> StyleProfile:
        profile = StyleProfile(
            project_id=project_id,
            reference_work_id=reference_work_id,
            author=author,
            reference_title=reference_title,
            name=name,
            voice_summary=voice_summary,
            profile_json=profile_json,
            skill_markdown=skill_markdown,
            confirm_status=ConfirmStatus.DRAFT,
            lock_status=LockStatus.UNLOCKED,
        )
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def get_profile(self, profile_id: str) -> StyleProfile | None:
        return self.db.get(StyleProfile, profile_id)

    def list_profiles(self, project_id: str | None = None) -> list[StyleProfile]:
        stmt = select(StyleProfile)
        if project_id is not None:
            stmt = stmt.where(StyleProfile.project_id == project_id)
        stmt = stmt.order_by(StyleProfile.created_at.desc(), StyleProfile.author.asc())
        return list(self.db.scalars(stmt).all())

    def update_profile(self, profile: StyleProfile, **fields: object) -> StyleProfile:
        for key, value in fields.items():
            setattr(profile, key, value)
        _touch(profile)
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def delete_profile(self, profile: StyleProfile) -> None:
        self.db.delete(profile)
        self.db.commit()
