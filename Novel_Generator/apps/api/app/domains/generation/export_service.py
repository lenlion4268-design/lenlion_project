from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import ExportFormat
from app.core.errors import AppError, NotFoundError
from app.domains.assets.models import Volume
from app.domains.generation.epub_builder import build_epub
from app.domains.generation.models import Chapter
from app.domains.generation.repository import GenerationRepository
from app.domains.generation.schemas import ManuscriptExportResponse
from app.domains.projects.repository import ProjectRepository


@dataclass
class ExportFile:
    payload: bytes | str
    media_type: str
    filename: str
    chapter_count: int
    word_count: int


class ExportService:
    def __init__(
        self,
        db: Session,
        project_repo: ProjectRepository,
        generation_repo: GenerationRepository,
    ) -> None:
        self.db = db
        self.project_repo = project_repo
        self.generation_repo = generation_repo

    def export_manuscript(
        self,
        project_id: str,
        *,
        volume_id: str | None = None,
        include_drafts: bool = False,
        export_format: str = "markdown",
    ) -> ManuscriptExportResponse:
        export_file = self.build_export_file(
            project_id,
            volume_id=volume_id,
            include_drafts=include_drafts,
            export_format=export_format,
        )
        preview = ""
        if isinstance(export_file.payload, str):
            preview = export_file.payload[:500]
        elif export_format == ExportFormat.EPUB.value:
            preview = f"EPUB 文件，大小 {len(export_file.payload)} 字节"

        return ManuscriptExportResponse(
            project_id=project_id,
            volume_id=volume_id,
            format=export_format,
            chapter_count=export_file.chapter_count,
            content=preview,
            file_size=len(export_file.payload),
        )

    def build_export_file(
        self,
        project_id: str,
        *,
        volume_id: str | None = None,
        include_drafts: bool = False,
        export_format: str = "markdown",
    ) -> ExportFile:
        project = self.project_repo.get_by_id(project_id)
        if project is None:
            raise NotFoundError("Project not found")

        if volume_id is not None:
            volume = self.db.get(Volume, volume_id)
            if volume is None or volume.project_id != project_id:
                raise NotFoundError("Volume not found")

        chapters = self.generation_repo.list_manuscript_chapters(
            project_id,
            volume_id=volume_id,
            include_drafts=include_drafts,
        )
        word_count = sum(len(chapter.content) for chapter in chapters)

        if export_format == ExportFormat.EPUB.value:
            binary = build_epub(project.title, chapters)
            suffix = volume_id or "all"
            return ExportFile(
                payload=binary,
                media_type="application/epub+zip",
                filename=f"{project_id}-{suffix}.epub",
                chapter_count=len(chapters),
                word_count=word_count,
            )

        markdown = self._render_markdown(project.title, chapters, volume_id=volume_id)
        if export_format == ExportFormat.TEXT.value:
            content = markdown.replace("# ", "").replace("## ", "").replace("---\n\n", "\n")
            ext = "txt"
            media_type = "text/plain; charset=utf-8"
        else:
            content = markdown
            ext = "md"
            media_type = "text/markdown; charset=utf-8"

        suffix = volume_id or "all"
        return ExportFile(
            payload=content,
            media_type=media_type,
            filename=f"{project_id}-{suffix}.{ext}",
            chapter_count=len(chapters),
            word_count=word_count,
        )

    def export_markdown_for_delivery(
        self,
        project_id: str,
        *,
        volume_id: str | None = None,
    ) -> str:
        project = self.project_repo.get_by_id(project_id)
        if project is None:
            raise NotFoundError("Project not found")
        chapters = self.generation_repo.list_manuscript_chapters(
            project_id,
            volume_id=volume_id,
            include_drafts=False,
        )
        return self._render_markdown(project.title, chapters, volume_id=volume_id)

    def _render_markdown(
        self,
        project_title: str,
        chapters: list[Chapter],
        *,
        volume_id: str | None,
    ) -> str:
        lines = [f"# {project_title}", ""]
        if not chapters:
            lines.append("（暂无已锁定章节可导出）")
            return "\n".join(lines)

        volume_titles: dict[str, str] = {}
        if volume_id is None:
            volume_ids = {chapter.volume_id for chapter in chapters}
            for vid in volume_ids:
                volume = self.db.get(Volume, vid)
                if volume is not None:
                    volume_titles[vid] = volume.title or f"第 {volume.volume_no} 卷"

        current_volume: str | None = None
        for chapter in chapters:
            if volume_id is None and chapter.volume_id != current_volume:
                current_volume = chapter.volume_id
                volume_title = volume_titles.get(chapter.volume_id, "未命名卷")
                lines.extend(["", f"## {volume_title}", ""])
            lines.extend(
                [
                    f"### {chapter.title or f'第 {chapter.chapter_no} 章'}",
                    "",
                    chapter.content.strip(),
                    "",
                    "---",
                    "",
                ]
            )
        return "\n".join(lines).strip() + "\n"
