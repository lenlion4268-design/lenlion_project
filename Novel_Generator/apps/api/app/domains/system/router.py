from fastapi import APIRouter

from app.core.config import settings
from app.domains.generation.worker import queue_status

router = APIRouter(tags=["system"])


@router.get(f"{settings.api_prefix}/health")
def health() -> dict:
    queue = queue_status()
    return {
        "status": "ok",
        "queue_backend": queue.get("backend", "thread"),
        "redis_connected": queue.get("redis_connected", False),
        "celery_broker_configured": queue.get("celery_broker_configured", False),
    }
