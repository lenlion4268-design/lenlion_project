from app.domains.publish.models import Publication


def build_platform_payload(
    publication: Publication,
    *,
    markdown_content: str,
    download_url: str,
    preset: str,
) -> dict[str, object]:
    base = {
        "publication_id": publication.id,
        "project_id": publication.project_id,
        "volume_id": publication.volume_id,
        "title": publication.title,
        "format": publication.format,
        "chapter_count": publication.chapter_count,
        "word_count": publication.word_count,
        "download_url": download_url,
    }
    if preset == "minimal":
        return base
    if preset == "full":
        return {**base, "content_markdown": markdown_content}
    return {**base, "content_markdown": markdown_content[:20000]}
