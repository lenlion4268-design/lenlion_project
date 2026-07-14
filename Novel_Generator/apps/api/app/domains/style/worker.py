from app.core.config import settings
from app.core.database import SessionLocal
from app.domains.generation.queue import get_job_queue
from app.domains.system.queue_dispatcher import format_queue_message


def process_style_analysis(job_id: str) -> None:
    from app.domains.projects.repository import ProjectRepository
    from app.domains.style.repository import StyleRepository
    from app.domains.style.service import StyleService

    db = SessionLocal()
    try:
        service = StyleService(db, ProjectRepository(db), StyleRepository(db))
        service.execute_analysis(job_id)
    finally:
        db.close()


def enqueue_style_analysis(job_id: str) -> None:
    if settings.style_analysis_force_sync:
        process_style_analysis(job_id)
        return
    message = format_queue_message("style", job_id)
    queue = get_job_queue()
    task_id = queue.enqueue(message)
    if task_id:
        from app.domains.style.repository import StyleRepository

        db = SessionLocal()
        try:
            repo = StyleRepository(db)
            job = repo.get_analysis_job(job_id)
            if job is not None:
                repo.update_analysis_job(job, queue_task_id=task_id)
        finally:
            db.close()
