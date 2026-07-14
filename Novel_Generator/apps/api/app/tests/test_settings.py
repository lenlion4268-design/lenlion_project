from app.core.config import settings


def test_get_settings_masks_api_key(client) -> None:
    patch = client.patch(
        f"{settings.api_prefix}/settings/models",
        json={"openai_api_key": "sk-test-secret-key-1234"},
    )
    assert patch.status_code == 200

    response = client.get(f"{settings.api_prefix}/settings")
    assert response.status_code == 200
    data = response.json()
    assert data["models"]["openai_api_key_masked"] == "sk-***1234"
    assert "sk-test-secret-key-1234" not in str(data)


def test_patch_personal_settings(client) -> None:
    response = client.patch(
        f"{settings.api_prefix}/settings/personal",
        json={"display_name": "测试作者", "pen_name": "笔名甲", "bio": "简介"},
    )
    assert response.status_code == 200
    personal = response.json()["personal"]
    assert personal["display_name"] == "测试作者"
    assert personal["pen_name"] == "笔名甲"


def test_patch_models_updates_effective_settings(client) -> None:
    response = client.patch(
        f"{settings.api_prefix}/settings/models",
        json={
            "ai_provider": "mock",
            "ai_model": "custom-model",
            "ai_model_chapter": "chapter-override",
            "default_model_profile": "fast",
        },
    )
    assert response.status_code == 200
    assert response.json()["models"]["ai_model"] == "custom-model"

    effective = client.get(f"{settings.api_prefix}/settings/models/effective")
    assert effective.status_code == 200
    rows = effective.json()["rows"]
    chapter_default = next(
        row for row in rows if row["target_stage"] == "chapters" and row["model_profile"] == "default"
    )
    assert chapter_default["model_name"] == "chapter-override"


def test_model_connection_mock(client) -> None:
    response = client.post(f"{settings.api_prefix}/settings/models/test")
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_delete_locked_profile_forbidden(client) -> None:
    upload = client.post(
        f"{settings.api_prefix}/materials/references/upload",
        data={"author": "作者", "title": "作品"},
        files={"file": ("ref.txt", ("content" * 100).encode(), "text/plain")},
    )
    reference_id = upload.json()["id"]
    client.post(f"{settings.api_prefix}/materials/references/{reference_id}/analyze")
    profile_id = client.get(f"{settings.api_prefix}/materials/style-profiles").json()["items"][0]["id"]
    client.post(f"{settings.api_prefix}/materials/style-profiles/{profile_id}/lock")

    delete = client.delete(f"{settings.api_prefix}/materials/style-profiles/{profile_id}")
    assert delete.status_code == 403

    client.post(f"{settings.api_prefix}/materials/style-profiles/{profile_id}/unlock")
    delete = client.delete(f"{settings.api_prefix}/materials/style-profiles/{profile_id}")
    assert delete.status_code == 204
