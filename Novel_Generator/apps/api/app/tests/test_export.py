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
        json={"content": "成稿正文第一段。"},
    )
    _lock_asset(client, ReviewTargetType.CHAPTER, chapter_id)
    return volume["id"], chapter_id


def test_export_locked_chapters_only(client) -> None:
    project_id = _create_project(client, title="导出测试")

    response = client.get(f"{settings.api_prefix}/projects/{project_id}/export")
    assert response.status_code == 200
    data = response.json()
    assert data["chapter_count"] == 0
    assert "暂无已锁定章节" in data["content"]


def test_export_includes_locked_chapter(client) -> None:
    project_id = _create_project(client, title="成稿导出")
    volume_id, _ = _setup_locked_chapter(client, project_id)

    response = client.get(
        f"{settings.api_prefix}/projects/{project_id}/export",
        params={"volume_id": volume_id},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["chapter_count"] == 1
    assert "成稿正文第一段。" in data["content"]
    assert "成稿导出" in data["content"]


def test_export_download_returns_attachment(client) -> None:
    project_id = _create_project(client, title="下载导出")
    volume_id, _ = _setup_locked_chapter(client, project_id)

    response = client.get(
        f"{settings.api_prefix}/projects/{project_id}/export/download",
        params={"volume_id": volume_id},
    )
    assert response.status_code == 200
    assert "attachment" in response.headers.get("content-disposition", "")
    assert "成稿正文第一段。" in response.text
