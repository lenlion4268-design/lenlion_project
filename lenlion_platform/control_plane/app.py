from __future__ import annotations

from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="lenlion-control-plane")

    @app.get("/healthz")
    def healthz() -> dict[str, str | bool]:
        return {"ok": True, "service": "control-plane"}

    return app
