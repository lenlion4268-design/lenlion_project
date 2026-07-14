from app.domains.generation.celery_app import celery
from app.domains.system.queue_dispatcher import dispatch_queue_message


@celery.task(name="novel.generation.process")
def process_generation_job_task(job_id: str) -> None:
    from app.domains.generation.worker import process_generation_job

    process_generation_job(job_id)


@celery.task(name="novel.queue.process")
def process_queue_message_task(message: str) -> None:
    dispatch_queue_message(message)
