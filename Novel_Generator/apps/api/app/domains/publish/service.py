from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import DeliveryStatus, ExportFormat, PublicationStatus, PublishChannel
from app.core.errors import AppError, ForbiddenError, NotFoundError
from app.domains.assets.models import Volume
from app.domains.generation.export_service import ExportFile, ExportService
from app.domains.publish.delivery import WebhookDelivery
from app.domains.publish.models import Publication
from app.domains.publish.platform_delivery import PlatformDelivery
from app.domains.publish.schemas import PublicationListResponse, PublicationResponse, PublishRequest
from app.domains.projects.repository import ProjectRepository


class PublishRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, publication: Publication) -> Publication:
        self.db.add(publication)
        self.db.commit()
        self.db.refresh(publication)
        return publication

    def list_by_project(self, project_id: str) -> list[Publication]:
        stmt = (
            select(Publication)
            .where(Publication.project_id == project_id)
            .order_by(Publication.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def get(self, publication_id: str) -> Publication | None:
        return self.db.get(Publication, publication_id)


class PublishService:
    def __init__(
        self,
        db: Session,
        project_repo: ProjectRepository,
        publish_repo: PublishRepository,
        export_service: ExportService,
        webhook_delivery: WebhookDelivery | None = None,
        platform_delivery: PlatformDelivery | None = None,
    ) -> None:
        self.db = db
        self.project_repo = project_repo
        self.publish_repo = publish_repo
        self.export_service = export_service
        self.webhook_delivery = webhook_delivery or WebhookDelivery()
        self.platform_delivery = platform_delivery or PlatformDelivery()

    def publish(self, project_id: str, data: PublishRequest) -> PublicationResponse:
        project = self.project_repo.get_by_id(project_id)
        if project is None:
            raise NotFoundError("Project not found")

        if data.channel == PublishChannel.WEBHOOK and not settings.publish_webhook_url:
            raise AppError(503, "PUBLISH_WEBHOOK_URL is not configured")
        if data.channel == PublishChannel.PLATFORM and not settings.publish_platform_api_url:
            raise AppError(503, "PUBLISH_PLATFORM_API_URL is not configured")

        export_file = self.export_service.build_export_file(
            project_id,
            volume_id=data.volume_id,
            include_drafts=False,
            export_format=data.export_format,
        )
        if export_file.chapter_count == 0:
            raise ForbiddenError("No locked chapters available for publication")

        volume_title = ""
        if data.volume_id:
            volume = self.db.get(Volume, data.volume_id)
            if volume is None or volume.project_id != project_id:
                raise NotFoundError("Volume not found")
            volume_title = volume.title

        title = data.title or volume_title or f"{project.title} 成稿"
        storage_dir = Path(settings.local_storage_dir) / project_id / "publications"
        storage_dir.mkdir(parents=True, exist_ok=True)

        publication = Publication(
            project_id=project_id,
            volume_id=data.volume_id,
            title=title,
            format=data.export_format,
            status=PublicationStatus.PUBLISHED,
            storage_path="",
            chapter_count=export_file.chapter_count,
            word_count=export_file.word_count,
            channel=data.channel,
            delivery_status=DeliveryStatus.SKIPPED,
            published_at=datetime.now(UTC),
        )
        self.publish_repo.create(publication)

        file_path = storage_dir / f"{publication.id}.{self._file_extension(data.export_format)}"
        self._write_export_file(file_path, export_file)
        publication.storage_path = str(file_path)

        download_url = f"{settings.api_prefix}/publications/{publication.id}/download"
        if data.channel == PublishChannel.WEBHOOK:
            markdown = self._delivery_markdown(project_id, data, export_file)
            publication.delivery_status = DeliveryStatus.PENDING
            external_ref, error = self.webhook_delivery.deliver(
                publication,
                content=markdown,
                download_url=download_url,
            )
            self._apply_delivery_result(publication, external_ref, error)
        elif data.channel == PublishChannel.PLATFORM:
            markdown = self._delivery_markdown(project_id, data, export_file)
            publication.delivery_status = DeliveryStatus.PENDING
            external_ref, error = self.platform_delivery.deliver(
                publication,
                markdown_content=markdown,
                download_url=download_url,
            )
            self._apply_delivery_result(publication, external_ref, error)

        self.db.commit()
        self.db.refresh(publication)
        return PublicationResponse.model_validate(publication)

    def list_publications(self, project_id: str) -> PublicationListResponse:
        if self.project_repo.get_by_id(project_id) is None:
            raise NotFoundError("Project not found")
        items = [
            PublicationResponse.model_validate(item)
            for item in self.publish_repo.list_by_project(project_id)
        ]
        return PublicationListResponse(items=items, total=len(items))

    def get_publication(self, publication_id: str) -> PublicationResponse:
        publication = self.publish_repo.get(publication_id)
        if publication is None:
            raise NotFoundError("Publication not found")
        return PublicationResponse.model_validate(publication)

    def retry_delivery(self, publication_id: str) -> PublicationResponse:
        publication = self.publish_repo.get(publication_id)
        if publication is None:
            raise NotFoundError("Publication not found")
        if publication.channel not in (PublishChannel.WEBHOOK, PublishChannel.PLATFORM):
            raise ForbiddenError("Only webhook or platform publications support delivery retry")
        if publication.delivery_status == DeliveryStatus.SUCCEEDED:
            raise ForbiddenError("Delivery already succeeded")

        markdown = self.export_service.export_markdown_for_delivery(
            publication.project_id,
            volume_id=publication.volume_id,
        )
        download_url = f"{settings.api_prefix}/publications/{publication.id}/download"
        publication.delivery_status = DeliveryStatus.PENDING
        publication.delivery_error = None

        if publication.channel == PublishChannel.WEBHOOK:
            if not settings.publish_webhook_url:
                raise AppError(503, "PUBLISH_WEBHOOK_URL is not configured")
            external_ref, error = self.webhook_delivery.deliver(
                publication,
                content=markdown,
                download_url=download_url,
            )
        else:
            if not settings.publish_platform_api_url:
                raise AppError(503, "PUBLISH_PLATFORM_API_URL is not configured")
            external_ref, error = self.platform_delivery.deliver(
                publication,
                markdown_content=markdown,
                download_url=download_url,
            )
        self._apply_delivery_result(publication, external_ref, error)
        self.db.commit()
        self.db.refresh(publication)
        return PublicationResponse.model_validate(publication)

    def read_publication_file(self, publication_id: str) -> tuple[bytes | str, str, str]:
        publication = self.publish_repo.get(publication_id)
        if publication is None:
            raise NotFoundError("Publication not found")
        path = Path(publication.storage_path)
        if not path.exists():
            raise NotFoundError("Publication file not found")
        if publication.format == ExportFormat.EPUB.value:
            return path.read_bytes(), "application/epub+zip", f"{publication.id}.epub"
        content = path.read_text(encoding="utf-8")
        ext = "md" if publication.format == ExportFormat.MARKDOWN.value else "txt"
        media_type = (
            "text/markdown; charset=utf-8"
            if ext == "md"
            else "text/plain; charset=utf-8"
        )
        return content, media_type, f"{publication.id}.{ext}"

    @staticmethod
    def _file_extension(export_format: str) -> str:
        if export_format == ExportFormat.EPUB.value:
            return "epub"
        if export_format == ExportFormat.TEXT.value:
            return "txt"
        return "md"

    @staticmethod
    def _write_export_file(path: Path, export_file: ExportFile) -> None:
        if isinstance(export_file.payload, bytes):
            path.write_bytes(export_file.payload)
        else:
            path.write_text(export_file.payload, encoding="utf-8")

    def _delivery_markdown(
        self,
        project_id: str,
        data: PublishRequest,
        export_file: ExportFile,
    ) -> str:
        if isinstance(export_file.payload, str):
            return export_file.payload
        return self.export_service.export_markdown_for_delivery(
            project_id,
            volume_id=data.volume_id,
        )

    @staticmethod
    def _apply_delivery_result(
        publication: Publication,
        external_ref: str | None,
        error: str | None,
    ) -> None:
        if error:
            publication.delivery_status = DeliveryStatus.FAILED
            publication.delivery_error = error
        else:
            publication.delivery_status = DeliveryStatus.SUCCEEDED
            publication.external_ref = external_ref
