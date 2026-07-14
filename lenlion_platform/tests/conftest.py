from __future__ import annotations

import pytest

from control_plane import store


@pytest.fixture(autouse=True)
def memory_store(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:
    if request.node.get_closest_marker("postgres_smoke"):
        yield
        return

    monkeypatch.setenv("LENLION_PLATFORM_USE_MEMORY", "1")
    monkeypatch.setenv("PLATFORM_JWT_SECRET", "test-platform-jwt-secret-32bytes-min")
    monkeypatch.setenv("ADMIN_TOKEN", "test-admin-token-32bytes-minimum")
    monkeypatch.setenv("DATABASE_URL", "postgresql://unused/unused")
    monkeypatch.setenv("OPENAI_COMPAT_BASE_URL", "https://upstream.example/v1")
    monkeypatch.setenv("UPSTREAM_OPENAI_API_KEY", "sk-test-upstream")
    store.reset_memory_store()
    yield
    store.reset_memory_store()
