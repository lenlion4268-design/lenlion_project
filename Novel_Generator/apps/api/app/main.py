from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import SessionLocal
from app.domains.assets.router import router as assets_router
from app.domains.generation.router import router as generation_router
from app.domains.projects.router import router as projects_router
from app.domains.publish.router import router as publish_router
from app.domains.review.router import router as review_router
from app.domains.settings.router import router as settings_router
from app.domains.settings.service import SettingsService
from app.domains.style.router import router as style_router
from app.domains.system.router import router as system_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    db = SessionLocal()
    try:
        SettingsService(db).bootstrap()
    finally:
        db.close()
    yield


app = FastAPI(title="Novel Generator API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects_router)
app.include_router(assets_router)
app.include_router(review_router)
app.include_router(generation_router)
app.include_router(publish_router)
app.include_router(style_router)
app.include_router(settings_router)
app.include_router(system_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "novel-generator-api"}
