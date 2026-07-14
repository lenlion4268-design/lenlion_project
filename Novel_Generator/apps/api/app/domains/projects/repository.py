from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import ProjectStatus
from app.domains.projects.models import NovelProject
from app.domains.projects.schemas import ProjectCreate, ProjectUpdate


def _touch(entity: NovelProject) -> None:
    entity.updated_at = datetime.now(UTC)


class ProjectRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, data: ProjectCreate) -> NovelProject:
        project = NovelProject(
            title=data.title,
            genre=data.genre,
            mode=data.mode,
        )
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def get_by_id(self, project_id: str) -> NovelProject | None:
        return self.db.get(NovelProject, project_id)

    def list_projects(
        self,
        *,
        status: ProjectStatus | None = None,
    ) -> list[NovelProject]:
        stmt = select(NovelProject).order_by(NovelProject.updated_at.desc())
        if status is not None:
            stmt = stmt.where(NovelProject.status == status)
        return list(self.db.scalars(stmt).all())

    def update(self, project: NovelProject, data: ProjectUpdate) -> NovelProject:
        updates = data.model_dump(exclude_unset=True)
        for key, value in updates.items():
            setattr(project, key, value)
        _touch(project)
        self.db.commit()
        self.db.refresh(project)
        return project
