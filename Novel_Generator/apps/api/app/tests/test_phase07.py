import zipfile
from io import BytesIO
from unittest.mock import MagicMock, patch

from app.core.config import settings
from app.domains.generation.epub_builder import build_epub
from app.tests.test_export import _setup_locked_chapter
from app.tests.test_generation import _create_project


def test_build_epub_produces_valid_zip() -> None:
    class FakeChapter:
        title = "开篇"
        chapter_no = 1
        content = "第一段正文。\n第二段正文。"

    epub_bytes = build_epub("测试小说", [FakeChapter()])  # type: ignore[list-item]
    with zipfile.ZipFile(BytesIO(epub_bytes)) as archive:
        names = archive.namelist()
        assert "mimetype" in names
        assert archive.read("mimetype") == b"application/epub+zip"
        assert any(name.endswith(".xhtml") for name in names)


def test_export_epub_download(client) -> None:
    project_id = _create_project(client, title="EPUB 导出")
    volume_id, _ = _setup_locked_chapter(client, project_id)

    response = client.get(
        f"{settings.api_prefix}/projects/{project_id}/export/download",
        params={"volume_id": volume_id, "format": "epub"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/epub+zip")
    assert response.content[:2] == b"PK"


def test_export_epub_json_metadata(client) -> None:
    project_id = _create_project(client, title="EPUB 元数据")
    volume_id, _ = _setup_locked_chapter(client, project_id)

    response = client.get(
        f"{settings.api_prefix}/projects/{project_id}/export",
        params={"volume_id": volume_id, "format": "epub"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["chapter_count"] == 1
    assert data["file_size"] > 0
    assert "EPUB" in data["content"]


def test_platform_publish_delivers_and_records_status(client, monkeypatch) -> None:
    with patch("app.domains.publish.platform_delivery.httpx.post") as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.content = b'{"id":"platform-42"}'
        mock_response.json.return_value = {"id": "platform-42"}
        mock_post.return_value = mock_response

        monkeypatch.setattr(settings, "publish_platform_api_url", "https://platform.example/api/publish")
        monkeypatch.setattr(settings, "publish_platform_api_token", "secret-token")
        project_id = _create_project(client, title="平台发布")
        volume_id, _ = _setup_locked_chapter(client, project_id)

        response = client.post(
            f"{settings.api_prefix}/projects/{project_id}/publish",
            json={"volume_id": volume_id, "channel": "platform", "format": "epub"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["channel"] == "platform"
        assert data["format"] == "epub"
        assert data["delivery_status"] == "succeeded"
        assert data["external_ref"] == "platform-42"
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args.kwargs
        assert call_kwargs["headers"]["Authorization"] == "Bearer secret-token"


def test_platform_publish_requires_api_url(client) -> None:
    project_id = _create_project(client)
    response = client.post(
        f"{settings.api_prefix}/projects/{project_id}/publish",
        json={"channel": "platform", "format": "markdown"},
    )
    assert response.status_code == 503


def test_publication_epub_download(client, monkeypatch) -> None:
    monkeypatch.setattr(settings, "local_storage_dir", "/tmp/novel-generator-test")
    project_id = _create_project(client, title="EPUB 发布下载")
    volume_id, _ = _setup_locked_chapter(client, project_id)

    response = client.post(
        f"{settings.api_prefix}/projects/{project_id}/publish",
        json={"volume_id": volume_id, "channel": "local", "format": "epub"},
    )
    assert response.status_code == 201
    publication_id = response.json()["id"]

    download = client.get(f"{settings.api_prefix}/publications/{publication_id}/download")
    assert download.status_code == 200
    assert download.headers["content-type"].startswith("application/epub+zip")
    assert download.content[:2] == b"PK"
