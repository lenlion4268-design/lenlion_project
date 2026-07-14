from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

WEB_DIST = Path(__file__).resolve().parent / "web_dist"


def mount_admin_ui(app: FastAPI) -> None:
    if not WEB_DIST.is_dir() or not (WEB_DIST / "index.html").is_file():
        return

    assets_dir = WEB_DIST / "assets"
    if assets_dir.is_dir():
        app.mount("/admin-ui/assets", StaticFiles(directory=assets_dir), name="admin-ui-assets")

    @app.get("/admin-ui")
    @app.get("/admin-ui/")
    @app.get("/admin-ui/{path:path}")
    def serve_admin_ui(path: str = "") -> FileResponse:
        if path.startswith("assets/"):
            target = WEB_DIST / path
            if target.is_file():
                return FileResponse(target)
        return FileResponse(WEB_DIST / "index.html")
