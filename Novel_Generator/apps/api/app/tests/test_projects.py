import time

from app.core.config import settings
from app.core.enums import ConfirmStatus, ProjectMode, ProjectStage, ProjectStatus


def test_create_project_defaults(client) -> None:
    response = client.post(
        f"{settings.api_prefix}/projects",
        json={"title": "测试小说", "genre": "玄幻", "mode": ProjectMode.LONG},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "测试小说"
    assert data["genre"] == "玄幻"
    assert data["mode"] == ProjectMode.LONG
    assert data["status"] == ProjectStatus.ACTIVE
    assert data["current_stage"] == ProjectStage.CHARACTERS


def test_list_projects_sorted_by_updated_at(client) -> None:
    first = client.post(
        f"{settings.api_prefix}/projects",
        json={"title": "第一本", "genre": "都市", "mode": ProjectMode.SHORT},
    ).json()
    time.sleep(0.01)
    second = client.post(
        f"{settings.api_prefix}/projects",
        json={"title": "第二本", "genre": "科幻", "mode": ProjectMode.LONG},
    ).json()
    client.patch(
        f"{settings.api_prefix}/projects/{first['id']}",
        json={"title": "第一本（已更新）"},
    )

    response = client.get(f"{settings.api_prefix}/projects")
    assert response.status_code == 200
    items = response.json()["items"]
    assert items[0]["id"] == first["id"]
    assert items[1]["id"] == second["id"]


def test_list_projects_filter_by_status(client) -> None:
    project = client.post(
        f"{settings.api_prefix}/projects",
        json={"title": "归档测试", "genre": "悬疑", "mode": ProjectMode.SHORT},
    ).json()
    client.patch(
        f"{settings.api_prefix}/projects/{project['id']}",
        json={"status": ProjectStatus.ARCHIVED},
    )

    active = client.get(f"{settings.api_prefix}/projects", params={"status": ProjectStatus.ACTIVE})
    archived = client.get(
        f"{settings.api_prefix}/projects", params={"status": ProjectStatus.ARCHIVED}
    )
    assert active.json()["total"] == 0
    assert archived.json()["total"] == 1


def test_character_card_created_as_draft(client) -> None:
    project_id = client.post(
        f"{settings.api_prefix}/projects",
        json={"title": "角色测试", "genre": "仙侠", "mode": ProjectMode.LONG},
    ).json()["id"]

    response = client.post(
        f"{settings.api_prefix}/projects/{project_id}/character-cards",
        json={
            "name": "林风",
            "profile_json": {
                "personality": "冷静",
                "goals": "复仇",
            },
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["confirm_status"] == ConfirmStatus.DRAFT
    assert data["profile_json"]["personality"] == "冷静"


def test_theme_profile_upsert_overwrites(client) -> None:
    project_id = client.post(
        f"{settings.api_prefix}/projects",
        json={"title": "主题测试", "genre": "历史", "mode": ProjectMode.LONG},
    ).json()["id"]

    client.put(
        f"{settings.api_prefix}/projects/{project_id}/theme-profile",
        json={"theme": "第一版主题", "genre": "历史"},
    )
    response = client.put(
        f"{settings.api_prefix}/projects/{project_id}/theme-profile",
        json={"theme": "第二版主题", "genre": "历史"},
    )
    assert response.status_code == 200
    assert response.json()["theme"] == "第二版主题"
    assert response.json()["confirm_status"] == ConfirmStatus.DRAFT

    fetched = client.get(f"{settings.api_prefix}/projects/{project_id}/theme-profile")
    assert fetched.json()["theme"] == "第二版主题"


def test_world_setting_upsert_overwrites(client) -> None:
    project_id = client.post(
        f"{settings.api_prefix}/projects",
        json={"title": "世界观测试", "genre": "奇幻", "mode": ProjectMode.LONG},
    ).json()["id"]

    client.put(
        f"{settings.api_prefix}/projects/{project_id}/world-setting",
        json={"background_json": {"era": "古代"}},
    )
    response = client.put(
        f"{settings.api_prefix}/projects/{project_id}/world-setting",
        json={"background_json": {"era": "近未来", "power_system": "灵能"}},
    )
    assert response.json()["background_json"]["era"] == "近未来"
    assert response.json()["confirm_status"] == ConfirmStatus.DRAFT


def test_outline_and_volume_list(client) -> None:
    project_id = client.post(
        f"{settings.api_prefix}/projects",
        json={"title": "大纲测试", "genre": "玄幻", "mode": ProjectMode.LONG},
    ).json()["id"]

    outline = client.post(
        f"{settings.api_prefix}/projects/{project_id}/outlines",
        json={"title": "主线大纲", "summary": "少年成长"},
    ).json()
    assert outline["confirm_status"] == ConfirmStatus.DRAFT

    volume = client.post(
        f"{settings.api_prefix}/projects/{project_id}/volumes",
        json={"title": "第一卷", "outline_id": outline["id"], "volume_no": 1},
    ).json()
    assert volume["confirm_status"] == ConfirmStatus.DRAFT

    outlines = client.get(f"{settings.api_prefix}/projects/{project_id}/outlines").json()
    volumes = client.get(f"{settings.api_prefix}/projects/{project_id}/volumes").json()
    assert outlines["total"] == 1
    assert volumes["total"] == 1
