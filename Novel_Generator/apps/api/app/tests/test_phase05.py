import tempfile
from pathlib import Path

from app.core.config import settings
from app.core.enums import ReadinessStage, ReviewTargetType
from app.tests.test_generation import _create_project, _first_job, _lock_asset


def _setup_locked_chapter(client, project_id: str) -> tuple[str, str]:
    theme = client.put(
        f"{settings.api_prefix}/projects/{project_id}/theme-profile",
        json={"theme": "成长"},
    ).json()
    world = client.put(
        f"{settings.api_prefix}/projects/{project_id}/world-setting",
        json={"background_json": {}},
    ).json()
    outline = client.post(
        f"{settings.api_prefix}/projects/{project_id}/outlines",
        json={"title": "主线"},
    ).json()
    card = client.post(
        f"{settings.api_prefix}/projects/{project_id}/character-cards",
        json={"name": "林风"},
    ).json()
    client.post(
        f"{settings.api_prefix}/review/confirm",
        json={"target_type": ReviewTargetType.CHARACTER_CARD, "target_id": card["id"]},
    )
    volume = client.post(
        f"{settings.api_prefix}/projects/{project_id}/volumes",
        json={"title": "第一卷", "involved_characters": ["林风"], "outline_id": outline["id"]},
    ).json()
    for target_type, target_id in [
        (ReviewTargetType.THEME_PROFILE, theme["id"]),
        (ReviewTargetType.WORLD_SETTING, world["id"]),
        (ReviewTargetType.OUTLINE, outline["id"]),
        (ReviewTargetType.VOLUME, volume["id"]),
    ]:
        _lock_asset(client, target_type, target_id)

    job = _first_job(
        client.post(
            f"{settings.api_prefix}/projects/{project_id}/generation",
            json={"target_stage": ReadinessStage.CHAPTERS, "volume_id": volume["id"]},
        ).json()
    )
    chapter_id = job["result_id"]
    client.patch(
        f"{settings.api_prefix}/chapters/{chapter_id}",
        json={"content": "成稿正文。"},
    )
    _lock_asset(client, ReviewTargetType.CHAPTER, chapter_id)
    return volume["id"], chapter_id


def test_async_generation_completes_with_force_sync(client, monkeypatch) -> None:
    project_id = _create_project(client)
    volume_id, _ = _setup_locked_chapter(client, project_id)

    response = client.post(
        f"{settings.api_prefix}/projects/{project_id}/generation",
        json={
            "target_stage": ReadinessStage.CHAPTERS,
            "volume_id": volume_id,
            "async_mode": True,
            "model_profile": "fast",
        },
    )
    assert response.status_code == 201
    job = response.json()["jobs"][0]
    assert job["execution_mode"] == "async"
    assert job["model_profile"] == "fast"
    assert job["status"] == "succeeded"


def test_publish_creates_publication_file(client, monkeypatch) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr(settings, "local_storage_dir", tmpdir)
        project_id = _create_project(client, title="发布测试")
        volume_id, _ = _setup_locked_chapter(client, project_id)

        response = client.post(
            f"{settings.api_prefix}/projects/{project_id}/publish",
            json={"volume_id": volume_id, "title": "第一卷成稿", "format": "markdown"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["chapter_count"] == 1
        assert Path(data["storage_path"]).exists()

        listing = client.get(f"{settings.api_prefix}/projects/{project_id}/publications").json()
        assert listing["total"] == 1

        download = client.get(
            f"{settings.api_prefix}/publications/{data['id']}/download",
        )
        assert download.status_code == 200
        assert "成稿正文。" in download.text


def test_publish_blocked_without_locked_chapters(client) -> None:
    project_id = _create_project(client)
    response = client.post(
        f"{settings.api_prefix}/projects/{project_id}/publish",
        json={"format": "markdown"},
    )
    assert response.status_code == 403
