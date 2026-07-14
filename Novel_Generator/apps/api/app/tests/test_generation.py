from app.core.config import settings
from app.core.enums import ConfirmStatus, LockStatus, ReadinessStage, ReviewTargetType


def _create_project(client, title: str = "测试小说") -> str:
    response = client.post(
        f"{settings.api_prefix}/projects",
        json={"title": title, "genre": "玄幻", "mode": "long"},
    )
    return response.json()["id"]


def _confirm_theme(client, project_id: str) -> str:
    profile = client.put(
        f"{settings.api_prefix}/projects/{project_id}/theme-profile",
        json={"theme": "成长", "genre": "玄幻"},
    ).json()
    client.post(
        f"{settings.api_prefix}/review/confirm",
        json={"target_type": ReviewTargetType.THEME_PROFILE, "target_id": profile["id"]},
    )
    return profile["id"]


def _confirm_world(client, project_id: str) -> str:
    setting = client.put(
        f"{settings.api_prefix}/projects/{project_id}/world-setting",
        json={"background_json": {"era": "古代"}},
    ).json()
    client.post(
        f"{settings.api_prefix}/review/confirm",
        json={"target_type": ReviewTargetType.WORLD_SETTING, "target_id": setting["id"]},
    )
    return setting["id"]


def _confirm_character(client, project_id: str, name: str = "林风") -> str:
    card = client.post(
        f"{settings.api_prefix}/projects/{project_id}/character-cards",
        json={"name": name, "profile_json": {"goals": "复仇"}},
    ).json()
    client.post(
        f"{settings.api_prefix}/review/confirm",
        json={"target_type": ReviewTargetType.CHARACTER_CARD, "target_id": card["id"]},
    )
    return card["id"]


def _lock_asset(client, target_type: str, target_id: str) -> None:
    client.post(
        f"{settings.api_prefix}/review/lock",
        json={"target_type": target_type, "target_id": target_id},
    )


def _first_job(payload: dict) -> dict:
    return payload["jobs"][0]


def test_outline_generation_blocked_without_readiness(client) -> None:
    project_id = _create_project(client)

    response = client.post(
        f"{settings.api_prefix}/projects/{project_id}/generation",
        json={"target_stage": ReadinessStage.OUTLINE},
    )
    assert response.status_code == 403


def test_outline_generation_creates_draft_outline(client) -> None:
    project_id = _create_project(client)
    _confirm_theme(client, project_id)
    _confirm_world(client, project_id)
    _confirm_character(client, project_id)

    response = client.post(
        f"{settings.api_prefix}/projects/{project_id}/generation",
        json={"target_stage": ReadinessStage.OUTLINE},
    )
    assert response.status_code == 201
    job = _first_job(response.json())
    assert job["status"] == "succeeded"
    assert job["result_type"] == ReviewTargetType.OUTLINE
    assert job["result_id"]

    outlines = client.get(f"{settings.api_prefix}/projects/{project_id}/outlines").json()
    assert outlines["total"] == 1
    assert outlines["items"][0]["confirm_status"] == ConfirmStatus.DRAFT
    assert "AI 大纲草案" in outlines["items"][0]["title"]


def test_volume_generation_requires_locked_outline(client) -> None:
    project_id = _create_project(client)
    outline = client.post(
        f"{settings.api_prefix}/projects/{project_id}/outlines",
        json={"title": "主线", "summary": "摘要"},
    ).json()

    response = client.post(
        f"{settings.api_prefix}/projects/{project_id}/generation",
        json={"target_stage": ReadinessStage.VOLUMES, "outline_id": outline["id"]},
    )
    assert response.status_code == 403


def test_volume_generation_creates_draft_volume(client) -> None:
    project_id = _create_project(client)
    outline = client.post(
        f"{settings.api_prefix}/projects/{project_id}/outlines",
        json={"title": "主线", "summary": "摘要"},
    ).json()
    _lock_asset(client, ReviewTargetType.OUTLINE, outline["id"])

    response = client.post(
        f"{settings.api_prefix}/projects/{project_id}/generation",
        json={"target_stage": ReadinessStage.VOLUMES, "outline_id": outline["id"]},
    )
    assert response.status_code == 201
    job = _first_job(response.json())
    assert job["status"] == "succeeded"
    assert job["result_type"] == ReviewTargetType.VOLUME

    volumes = client.get(f"{settings.api_prefix}/projects/{project_id}/volumes").json()
    assert volumes["total"] == 1
    assert volumes["items"][0]["volume_no"] == 1


def test_chapter_generation_creates_editable_draft(client) -> None:
    project_id = _create_project(client)
    theme = client.put(
        f"{settings.api_prefix}/projects/{project_id}/theme-profile",
        json={"theme": "成长", "genre": "玄幻"},
    ).json()
    world = client.put(
        f"{settings.api_prefix}/projects/{project_id}/world-setting",
        json={"background_json": {"era": "古代"}},
    ).json()
    outline = client.post(
        f"{settings.api_prefix}/projects/{project_id}/outlines",
        json={"title": "主线", "summary": "摘要"},
    ).json()
    card = client.post(
        f"{settings.api_prefix}/projects/{project_id}/character-cards",
        json={"name": "林风", "profile_json": {"goals": "复仇"}},
    ).json()
    client.post(
        f"{settings.api_prefix}/review/confirm",
        json={"target_type": ReviewTargetType.CHARACTER_CARD, "target_id": card["id"]},
    )
    volume = client.post(
        f"{settings.api_prefix}/projects/{project_id}/volumes",
        json={
            "title": "第一卷",
            "volume_no": 1,
            "involved_characters": ["林风"],
            "outline_id": outline["id"],
        },
    ).json()

    for target_type, target_id in [
        (ReviewTargetType.THEME_PROFILE, theme["id"]),
        (ReviewTargetType.WORLD_SETTING, world["id"]),
        (ReviewTargetType.OUTLINE, outline["id"]),
        (ReviewTargetType.VOLUME, volume["id"]),
    ]:
        _lock_asset(client, target_type, target_id)

    response = client.post(
        f"{settings.api_prefix}/projects/{project_id}/generation",
        json={"target_stage": ReadinessStage.CHAPTERS, "volume_id": volume["id"]},
    )
    assert response.status_code == 201
    job = _first_job(response.json())
    assert job["status"] == "succeeded"
    chapter_id = job["result_id"]

    chapters = client.get(
        f"{settings.api_prefix}/projects/{project_id}/chapters",
        params={"volume_id": volume["id"]},
    ).json()
    assert chapters["total"] == 1
    assert chapters["items"][0]["source_type"] == "ai_suggested"

    patch = client.patch(
        f"{settings.api_prefix}/chapters/{chapter_id}",
        json={"content": "修订后的章节正文。"},
    )
    assert patch.status_code == 200
    assert patch.json()["content"] == "修订后的章节正文。"
    assert patch.json()["word_count"] == len("修订后的章节正文。")


def test_locked_chapter_cannot_be_edited(client) -> None:
    project_id = _create_project(client)
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
    _lock_asset(client, ReviewTargetType.CHAPTER, chapter_id)

    response = client.patch(
        f"{settings.api_prefix}/chapters/{chapter_id}",
        json={"content": "尝试修改"},
    )
    assert response.status_code == 403
