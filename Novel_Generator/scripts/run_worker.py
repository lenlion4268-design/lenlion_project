#!/usr/bin/env python3
"""Run Redis-backed generation worker."""

from app.domains.generation.worker import run_redis_worker_loop


def main() -> None:
    print("Starting Novel Generator Redis worker...")
    run_redis_worker_loop()


if __name__ == "__main__":
    main()
