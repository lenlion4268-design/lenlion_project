from app.core.enums import ProjectStatus
from app.core.errors import NotFoundError
from app.domains.projects.models import NovelProject
from app.domains.projects.repository import ProjectRepository
from app.domains.projects.schemas import ProjectCreate, ProjectListResponse, ProjectResponse, ProjectUpdate


class ProjectService:
    def __init__(self, repo: ProjectRepository) -> None:
        self.repo = repo

    def create_project(self, data: ProjectCreate) -> ProjectResponse:
        project = self.repo.create(data)
        return ProjectResponse.model_validate(project)

    def get_project(self, project_id: str) -> ProjectResponse:
        project = self._require_project(project_id)
        return ProjectResponse.model_validate(project)

    def list_projects(self, status: ProjectStatus | None = None) -> ProjectListResponse:
        projects = self.repo.list_projects(status=status)
        items = [ProjectResponse.model_validate(p) for p in projects]
        return ProjectListResponse(items=items, total=len(items))

    def update_project(self, project_id: str, data: ProjectUpdate) -> ProjectResponse:
        project = self._require_project(project_id)
        updated = self.repo.update(project, data)
        return ProjectResponse.model_validate(updated)

    def _require_project(self, project_id: str) -> NovelProject:
        project = self.repo.get_by_id(project_id)
        if project is None:
            raise NotFoundError("Project not found")
        return project
