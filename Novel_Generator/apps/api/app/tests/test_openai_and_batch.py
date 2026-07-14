from unittest.mock import MagicMock, patch

from app.core.config import settings
from app.core.enums import ReadinessStage, ReviewTargetType
from app.domains.generation.ai_provider.openai import OpenAiCompatibleProvider
from app.domains.generation.context import GenerationContext
from app.domains.settings.effective import get_effective_settings
from app.tests.test_generation import _create_project, _first_job, _lock_asset


def test_openai_provider_parses_json_response() -> None:
    effective = get_effective_settings()
    effective.openai_api_key = "test-key"
    provider = OpenAiCompatibleProvider(model="gpt-test")
    ctx = GenerationContext(project=MagicMock(title="测试", genre="玄幻"))

    fake_response = MagicMock()
    fake_response.raise_for_status.return_value = None
    fake_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": (
                        '{"title":"AI 大纲","summary":"摘要","plot_nodes_json":[],'
                        '"character_arcs_json":[],"ending_direction":"结局"}'
                    )
                }
            }
        ]
    }

    with patch("app.domains.generation.ai_provider.openai.httpx.post", return_value=fake_response):
        draft = provider.generate_outline(ctx)

    assert draft.title == "AI 大纲"
    assert draft.summary == "摘要"


def test_openai_provider_requires_api_key() -> None:
    effective = get_effective_settings()
    effective.openai_api_key = None
    try:
        OpenAiCompatibleProvider()
        raise AssertionError("expected AppError")
    except Exception as exc:
        assert "OPENAI_API_KEY" in str(exc.detail)


def test_batch_chapter_generation(client) -> None:
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

    response = client.post(
        f"{settings.api_prefix}/projects/{project_id}/generation",
        json={
            "target_stage": ReadinessStage.CHAPTERS,
            "volume_id": volume["id"],
            "batch_count": 3,
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["total"] == 3
    assert len(payload["jobs"]) == 3

    chapters = client.get(
        f"{settings.api_prefix}/projects/{project_id}/chapters",
        params={"volume_id": volume["id"]},
    ).json()
    assert chapters["total"] == 3
