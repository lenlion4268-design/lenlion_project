from celery import Celery

from app.core.config import settings

celery = Celery("novel_generator")


def configure_celery() -> Celery:
    broker = settings.celery_broker_url or settings.redis_url
    if not broker:
        raise RuntimeError("CELERY_BROKER_URL or REDIS_URL is required for Celery")
    celery.conf.update(
        broker_url=broker,
        result_backend=settings.celery_result_backend or broker,
        task_default_queue=settings.celery_queue_name,
        task_acks_late=True,
        include=["app.domains.generation.tasks"],
    )
    return celery
