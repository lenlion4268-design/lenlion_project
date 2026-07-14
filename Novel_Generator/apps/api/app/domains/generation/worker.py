from app.core.config import settings
from app.core.database import SessionLocal
from app.core.enums import QueueBackend
from app.domains.generation.queue import RedisJobQueue, get_job_queue, resolve_queue_backend
from app.domains.generation.repository import GenerationRepository
from app.domains.system.queue_dispatcher import dispatch_queue_message, format_queue_message


def process_generation_job(job_id: str) -> None:
    from app.domains.generation.service import GenerationService
    from app.domains.assets.status_service import AssetStatusService
    from app.domains.projects.repository import ProjectRepository
    from app.domains.review.service import ReadinessService

    db = SessionLocal()
    try:
        service = GenerationService(
            db,
            ProjectRepository(db),
            GenerationRepository(db),
            ReadinessService(db, ProjectRepository(db)),
            AssetStatusService(db),
        )
        service.execute_job(job_id)
    finally:
        db.close()


def enqueue_generation_job(job_id: str) -> None:
    if settings.generation_force_sync:
        process_generation_job(job_id)
        return
    message = format_queue_message("generation", job_id)
    queue = get_job_queue()
    task_id = queue.enqueue(message)
    if task_id:
        db = SessionLocal()
        try:
            repo = GenerationRepository(db)
            job = repo.get_job(job_id)
            if job is not None:
                repo.update_job(job, queue_task_id=task_id)
        finally:
            db.close()


def revoke_generation_job(task_id: str) -> None:
    from app.domains.generation.celery_app import configure_celery

    app = configure_celery()
    app.control.revoke(task_id, terminate=False)


def run_redis_worker_loop(*, poll_timeout_seconds: int = 5) -> None:
    if not settings.redis_url:
        raise RuntimeError("REDIS_URL is required to run redis worker")
    queue = RedisJobQueue(settings.redis_url, settings.redis_queue_name)
    while True:
        message = queue.blocking_pop(timeout_seconds=poll_timeout_seconds)
        if message:
            dispatch_queue_message(message)


def queue_status() -> dict[str, str | bool]:
    backend = resolve_queue_backend()
    status: dict[str, str | bool] = {"backend": backend.value}
    if backend in (QueueBackend.REDIS, QueueBackend.CELERY) and settings.redis_url:
        try:
            queue = RedisJobQueue(settings.redis_url, settings.redis_queue_name)
            status["redis_connected"] = queue.ping()
        except Exception:  # noqa: BLE001 — health probe
            status["redis_connected"] = False
    if backend == QueueBackend.CELERY:
        broker = settings.celery_broker_url or settings.redis_url
        status["celery_broker_configured"] = bool(broker)
    return status
