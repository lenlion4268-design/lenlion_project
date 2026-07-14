import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import Base, get_db
from app.domains.settings.effective import reset_effective_settings
from app.domains.settings.service import SettingsService
from app.main import app

TEST_DATABASE_URL = "sqlite+pysqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_database(monkeypatch) -> None:
    monkeypatch.setattr(settings, "generation_force_sync", True)
    monkeypatch.setattr(settings, "style_analysis_force_sync", True)
    monkeypatch.setattr(settings, "local_storage_dir", "/tmp/novel-generator-test")
    monkeypatch.setattr("app.domains.generation.worker.SessionLocal", TestingSessionLocal)
    monkeypatch.setattr("app.domains.style.worker.SessionLocal", TestingSessionLocal)
    Base.metadata.create_all(bind=engine)
    bootstrap_session = TestingSessionLocal()
    try:
        SettingsService(bootstrap_session).bootstrap()
    finally:
        bootstrap_session.close()
    yield
    reset_effective_settings()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session() -> Session:
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session: Session) -> TestClient:
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
