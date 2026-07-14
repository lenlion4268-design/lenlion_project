from typing import Protocol

from app.core.config import settings
from app.core.enums import QueueBackend


class JobQueue(Protocol):
    def enqueue(self, message: str) -> str | None: ...

    @property
    def backend(self) -> QueueBackend: ...


class ThreadJobQueue:
    @property
    def backend(self) -> QueueBackend:
        return QueueBackend.THREAD

    def enqueue(self, message: str) -> str | None:
        from app.domains.system.queue_dispatcher import dispatch_queue_message

        import threading

        threading.Thread(target=dispatch_queue_message, args=(message,), daemon=True).start()
        return None


class RedisJobQueue:
    def __init__(self, redis_url: str, queue_name: str) -> None:
        import redis

        self._client = redis.Redis.from_url(redis_url, decode_responses=True)
        self._queue_name = queue_name

    @property
    def backend(self) -> QueueBackend:
        return QueueBackend.REDIS

    def enqueue(self, message: str) -> str | None:
        self._client.lpush(self._queue_name, message)
        return None

    def blocking_pop(self, timeout_seconds: int = 5) -> str | None:
        item = self._client.brpop(self._queue_name, timeout=timeout_seconds)
        if item is None:
            return None
        _, payload = item
        return payload

    def ping(self) -> bool:
        return bool(self._client.ping())


class CeleryJobQueue:
    @property
    def backend(self) -> QueueBackend:
        return QueueBackend.CELERY

    def enqueue(self, message: str) -> str | None:
        from app.domains.generation.celery_app import configure_celery
        from app.domains.generation.tasks import process_queue_message_task

        configure_celery()
        result = process_queue_message_task.delay(message)
        return result.id


def resolve_queue_backend() -> QueueBackend:
    configured = settings.generation_queue_backend.lower()
    if configured == QueueBackend.CELERY.value:
        return QueueBackend.CELERY
    if configured == QueueBackend.REDIS.value:
        return QueueBackend.REDIS
    if configured == QueueBackend.THREAD.value:
        return QueueBackend.THREAD
    if settings.celery_broker_url:
        return QueueBackend.CELERY
    if settings.redis_url:
        return QueueBackend.REDIS
    return QueueBackend.THREAD


def get_job_queue() -> JobQueue:
    backend = resolve_queue_backend()
    if backend == QueueBackend.CELERY:
        broker = settings.celery_broker_url or settings.redis_url
        if not broker:
            raise RuntimeError("CELERY_BROKER_URL or REDIS_URL is required for celery queue backend")
        return CeleryJobQueue()
    if backend == QueueBackend.REDIS:
        if not settings.redis_url:
            raise RuntimeError("REDIS_URL is required for redis queue backend")
        return RedisJobQueue(settings.redis_url, settings.redis_queue_name)
    return ThreadJobQueue()
