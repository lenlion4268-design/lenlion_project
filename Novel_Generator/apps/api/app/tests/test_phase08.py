import httpx
from unittest.mock import MagicMock, patch

from app.core.config import settings
from app.core.enums import ExecutionMode, GenerationJobStatus, ReadinessStage
from app.domains.generation.queue import CeleryJobQueue, resolve_queue_backend
from app.domains.generation.repository import GenerationRepository
from app.domains.publish.platform_payload import build_platform_payload
from app.tests.test_export import _setup_locked_chapter
from app.tests.test_generation import _create_project


def test_resolve_queue_backend_uses_celery_when_broker_configured(monkeypatch) -> None:
    monkeypatch.setattr(settings, "celery_broker_url", "redis://localhost:6379/1")
    monkeypatch.setattr(settings, "generation_queue_backend", "auto")
    assert resolve_queue_backend().value == "celery"


def test_celery_queue_enqueue_returns_task_id(monkeypatch) -> None:
    mock_result = MagicMock()
    mock_result.id = "celery-task-123"
    with patch("app.domains.generation.tasks.process_queue_message_task.delay", return_value=mock_result):
        with patch("app.domains.generation.celery_app.configure_celery"):
            task_id = CeleryJobQueue().enqueue("generation:job-abc")
    assert task_id == "celery-task-123"


def test_cancel_queued_job(client, db_session) -> None:
    project_id = _create_project(client, title="取消任务")
    repo = GenerationRepository(db_session)
    job = repo.create_job(
        project_id=project_id,
        target_stage=ReadinessStage.CHAPTERS.value,
        outline_id=None,
        volume_id=None,
        provider="mock",
        model_profile="default",
        model_name="mock-writer",
        execution_mode=ExecutionMode.ASYNC.value,
    )

    response = client.post(f"{settings.api_prefix}/generation/jobs/{job.id}/cancel")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == GenerationJobStatus.CANCELLED


def test_cancel_running_job_rejected(client, db_session) -> None:
    project_id = _create_project(client)
    repo = GenerationRepository(db_session)
    job = repo.create_job(
        project_id=project_id,
        target_stage=ReadinessStage.CHAPTERS.value,
        outline_id=None,
        volume_id=None,
        provider="mock",
        model_profile="default",
        model_name="mock-writer",
        execution_mode=ExecutionMode.ASYNC.value,
    )
    repo.update_job(job, status=GenerationJobStatus.RUNNING)

    response = client.post(f"{settings.api_prefix}/generation/jobs/{job.id}/cancel")
    assert response.status_code == 403


def test_cancel_revokes_celery_task(client, db_session, monkeypatch) -> None:
    monkeypatch.setattr(settings, "celery_broker_url", "redis://localhost:6379/1")
    monkeypatch.setattr(settings, "generation_queue_backend", "celery")
    with patch("app.domains.generation.worker.revoke_generation_job") as mock_revoke:
        project_id = _create_project(client)
        repo = GenerationRepository(db_session)
        job = repo.create_job(
            project_id=project_id,
            target_stage=ReadinessStage.CHAPTERS.value,
            outline_id=None,
            volume_id=None,
            provider="mock",
            model_profile="default",
            model_name="mock-writer",
            execution_mode=ExecutionMode.ASYNC.value,
        )
        repo.update_job(job, queue_task_id="celery-task-999")

        response = client.post(f"{settings.api_prefix}/generation/jobs/{job.id}/cancel")
        assert response.status_code == 200
        mock_revoke.assert_called_once_with("celery-task-999")


def test_health_reports_celery_backend(client, monkeypatch) -> None:
    monkeypatch.setattr(settings, "celery_broker_url", "redis://localhost:6379/1")
    monkeypatch.setattr(settings, "redis_url", "redis://localhost:6379/0")
    monkeypatch.setattr(settings, "generation_queue_backend", "auto")
    response = client.get(f"{settings.api_prefix}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["queue_backend"] == "celery"
    assert data["celery_broker_configured"] is True


def test_retry_webhook_delivery(client, monkeypatch) -> None:
    monkeypatch.setattr(settings, "publish_webhook_url", "https://example.com/hook")
    project_id = _create_project(client, title="重试投递")
    volume_id, _ = _setup_locked_chapter(client, project_id)

    with patch("app.domains.publish.delivery.httpx.post") as mock_post:
        mock_post.side_effect = httpx.ConnectError("connection failed", request=MagicMock())
        publish = client.post(
            f"{settings.api_prefix}/projects/{project_id}/publish",
            json={"volume_id": volume_id, "channel": "webhook", "format": "markdown"},
        )
        assert publish.status_code == 201
        assert publish.json()["delivery_status"] == "failed"
        publication_id = publish.json()["id"]

    with patch("app.domains.publish.delivery.httpx.post") as mock_retry:
        mock_retry_response = MagicMock()
        mock_retry_response.raise_for_status.return_value = None
        mock_retry_response.headers = {"X-Publication-Ref": "retry-456"}
        mock_retry.return_value = mock_retry_response

        response = client.post(
            f"{settings.api_prefix}/publications/{publication_id}/retry-delivery",
        )
        assert response.status_code == 200
        assert response.json()["delivery_status"] == "succeeded"
        assert response.json()["external_ref"] == "retry-456"


def test_platform_payload_minimal_preset() -> None:
    class FakePublication:
        id = "pub-1"
        project_id = "proj-1"
        volume_id = "vol-1"
        title = "测试"
        format = "markdown"
        chapter_count = 3
        word_count = 1200

    payload = build_platform_payload(
        FakePublication(),  # type: ignore[arg-type]
        markdown_content="# 正文",
        download_url="/api/publications/pub-1/download",
        preset="minimal",
    )
    assert "content_markdown" not in payload
    assert payload["download_url"] == "/api/publications/pub-1/download"


def test_platform_payload_full_preset() -> None:
    class FakePublication:
        id = "pub-2"
        project_id = "proj-2"
        volume_id = None
        title = "完整"
        format = "epub"
        chapter_count = 1
        word_count = 500

    payload = build_platform_payload(
        FakePublication(),  # type: ignore[arg-type]
        markdown_content="# 完整正文",
        download_url="/download",
        preset="full",
    )
    assert payload["content_markdown"] == "# 完整正文"
