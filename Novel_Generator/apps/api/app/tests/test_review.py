from sqlalchemy import select

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


def test_outline_readiness_blocked_without_confirmed_theme(client) -> None:
    project_id = _create_project(client)
    _confirm_world(client, project_id)
    _confirm_character(client, project_id)

    response = client.get(
        f"{settings.api_prefix}/projects/{project_id}/readiness/{ReadinessStage.OUTLINE}"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ready"] is False
    assert any(item["label"] == "主题题材" for item in data["missing_items"])


def test_outline_readiness_ready_when_prerequisites_met(client) -> None:
    project_id = _create_project(client)
    _confirm_theme(client, project_id)
    _confirm_world(client, project_id)
    _confirm_character(client, project_id)

    response = client.get(
        f"{settings.api_prefix}/projects/{project_id}/readiness/{ReadinessStage.OUTLINE}"
    )
    assert response.json()["ready"] is True


def test_volume_readiness_blocked_without_locked_outline(client) -> None:
    project_id = _create_project(client)
    outline = client.post(
        f"{settings.api_prefix}/projects/{project_id}/outlines",
        json={"title": "主线", "summary": "摘要"},
    ).json()

    response = client.get(
        f"{settings.api_prefix}/projects/{project_id}/readiness/{ReadinessStage.VOLUMES}",
        params={"outline_id": outline["id"]},
    )
    assert response.json()["ready"] is False


def test_volume_readiness_ready_with_locked_outline(client) -> None:
    project_id = _create_project(client)
    outline = client.post(
        f"{settings.api_prefix}/projects/{project_id}/outlines",
        json={"title": "主线", "summary": "摘要"},
    ).json()
    client.post(
        f"{settings.api_prefix}/review/lock",
        json={"target_type": ReviewTargetType.OUTLINE, "target_id": outline["id"]},
    )

    response = client.get(
        f"{settings.api_prefix}/projects/{project_id}/readiness/{ReadinessStage.VOLUMES}",
        params={"outline_id": outline["id"]},
    )
    assert response.json()["ready"] is True


def test_chapter_readiness_blocked_without_locked_volume(client) -> None:
    project_id = _create_project(client)
    theme_id = _confirm_theme(client, project_id)
    world_id = _confirm_world(client, project_id)
    client.post(
        f"{settings.api_prefix}/review/lock",
        json={"target_type": ReviewTargetType.THEME_PROFILE, "target_id": theme_id},
    )
    client.post(
        f"{settings.api_prefix}/review/lock",
        json={"target_type": ReviewTargetType.WORLD_SETTING, "target_id": world_id},
    )
    outline = client.post(
        f"{settings.api_prefix}/projects/{project_id}/outlines",
        json={"title": "主线"},
    ).json()
    client.post(
        f"{settings.api_prefix}/review/lock",
        json={"target_type": ReviewTargetType.OUTLINE, "target_id": outline["id"]},
    )
    volume = client.post(
        f"{settings.api_prefix}/projects/{project_id}/volumes",
        json={"title": "第一卷", "volume_no": 1},
    ).json()

    response = client.get(
        f"{settings.api_prefix}/projects/{project_id}/readiness/{ReadinessStage.CHAPTERS}",
        params={"volume_id": volume["id"]},
    )
    assert response.json()["ready"] is False


def test_locked_asset_cannot_be_edited(client) -> None:
    project_id = _create_project(client)
    card = client.post(
        f"{settings.api_prefix}/projects/{project_id}/character-cards",
        json={"name": "主角"},
    ).json()
    client.post(
        f"{settings.api_prefix}/review/lock",
        json={"target_type": ReviewTargetType.CHARACTER_CARD, "target_id": card["id"]},
    )

    response = client.patch(
        f"{settings.api_prefix}/character-cards/{card['id']}",
        json={"name": "新名字"},
    )
    assert response.status_code == 403


def test_review_action_creates_record(client, db_session) -> None:
    from app.domains.review.models import ReviewRecord

    project_id = _create_project(client)
    card = client.post(
        f"{settings.api_prefix}/projects/{project_id}/character-cards",
        json={"name": "配角"},
    ).json()
    client.post(
        f"{settings.api_prefix}/review/confirm",
        json={
            "target_type": ReviewTargetType.CHARACTER_CARD,
            "target_id": card["id"],
            "comment": "确认通过",
        },
    )

    records = list(db_session.scalars(select(ReviewRecord)).all())
    assert len(records) == 1
    assert records[0].action == "confirm"
    assert records[0].before_status == ConfirmStatus.DRAFT
    assert records[0].after_status == ConfirmStatus.CONFIRMED


def test_unlock_restores_editable_state(client) -> None:
    project_id = _create_project(client)
    card = client.post(
        f"{settings.api_prefix}/projects/{project_id}/character-cards",
        json={"name": "可解锁角色"},
    ).json()
    client.post(
        f"{settings.api_prefix}/review/lock",
        json={"target_type": ReviewTargetType.CHARACTER_CARD, "target_id": card["id"]},
    )
    unlock = client.post(
        f"{settings.api_prefix}/review/unlock",
        json={"target_type": ReviewTargetType.CHARACTER_CARD, "target_id": card["id"]},
    ).json()
    assert unlock["confirm_status"] == ConfirmStatus.CONFIRMED
    assert unlock["lock_status"] == LockStatus.UNLOCKED

    response = client.patch(
        f"{settings.api_prefix}/character-cards/{card['id']}",
        json={"name": "已解锁角色"},
    )
    assert response.status_code == 200
