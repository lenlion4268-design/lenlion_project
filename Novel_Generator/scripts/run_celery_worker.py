#!/usr/bin/env python3
"""Run Celery worker for generation tasks."""

from app.domains.generation.celery_app import celery, configure_celery


def main() -> None:
    configure_celery()
    print("Starting Novel Generator Celery worker...")
    celery.worker_main(argv=["worker", "--loglevel=info"])


if __name__ == "__main__":
    main()
