from unittest.mock import MagicMock, patch

from app.core.config import settings
from app.domains.generation.queue import RedisJobQueue, ThreadJobQueue, get_job_queue, resolve_queue_backend
from app.tests.test_phase05 import _setup_locked_chapter
from app.tests.test_generation import _create_project


def test_resolve_queue_backend_defaults_to_thread(monkeypatch) -> None:
    monkeypatch.setattr(settings, "redis_url", None)
    monkeypatch.setattr(settings, "generation_queue_backend", "auto")
    assert resolve_queue_backend().value == "thread"


def test_resolve_queue_backend_uses_redis_when_configured(monkeypatch) -> None:
    monkeypatch.setattr(settings, "redis_url", "redis://localhost:6379/0")
    monkeypatch.setattr(settings, "generation_queue_backend", "auto")
    assert resolve_queue_backend().value == "redis"


def test_get_job_queue_returns_thread_without_redis(monkeypatch) -> None:
    monkeypatch.setattr(settings, "redis_url", None)
    monkeypatch.setattr(settings, "generation_queue_backend", "thread")
    queue = get_job_queue()
    assert isinstance(queue, ThreadJobQueue)


def test_redis_queue_enqueue_calls_lpush(monkeypatch) -> None:
    fake_client = MagicMock()
    monkeypatch.setattr("redis.Redis.from_url", lambda *args, **kwargs: fake_client)
    queue = RedisJobQueue("redis://localhost:6379/0", "novel:generation")
    queue.enqueue("job-1")
    fake_client.lpush.assert_called_once_with("novel:generation", "job-1")


def test_health_reports_queue_backend(client, monkeypatch) -> None:
    monkeypatch.setattr(settings, "redis_url", None)
    response = client.get(f"{settings.api_prefix}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["queue_backend"] == "thread"


def test_webhook_publish_delivers_and_records_status(client, monkeypatch) -> None:
    with patch("app.domains.publish.delivery.httpx.post") as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.headers = {"X-Publication-Ref": "external-123"}
        mock_post.return_value = mock_response

        monkeypatch.setattr(settings, "publish_webhook_url", "https://example.com/hook")
        project_id = _create_project(client, title="Webhook 发布")
        volume_id, _ = _setup_locked_chapter(client, project_id)

        response = client.post(
            f"{settings.api_prefix}/projects/{project_id}/publish",
            json={"volume_id": volume_id, "channel": "webhook", "format": "markdown"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["channel"] == "webhook"
        assert data["delivery_status"] == "succeeded"
        assert data["external_ref"] == "external-123"
        mock_post.assert_called_once()


def test_webhook_publish_requires_webhook_url(client) -> None:
    project_id = _create_project(client)
    response = client.post(
        f"{settings.api_prefix}/projects/{project_id}/publish",
        json={"channel": "webhook", "format": "markdown"},
    )
    assert response.status_code == 503
