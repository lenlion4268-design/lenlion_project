GENERATION_PREFIX = "generation:"
STYLE_PREFIX = "style:"


def format_queue_message(kind: str, job_id: str) -> str:
    if kind == "style":
        return f"{STYLE_PREFIX}{job_id}"
    return f"{GENERATION_PREFIX}{job_id}"


def parse_queue_message(message: str) -> tuple[str, str]:
    if message.startswith(STYLE_PREFIX):
        return "style", message[len(STYLE_PREFIX) :]
    if message.startswith(GENERATION_PREFIX):
        return "generation", message[len(GENERATION_PREFIX) :]
    return "generation", message


def dispatch_queue_message(message: str) -> None:
    kind, job_id = parse_queue_message(message)
    if kind == "style":
        from app.domains.style.worker import process_style_analysis

        process_style_analysis(job_id)
        return
    from app.domains.generation.worker import process_generation_job

    process_generation_job(job_id)
