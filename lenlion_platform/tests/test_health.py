from fastapi.testclient import TestClient

from control_plane.app import create_app


def test_healthz_returns_ok() -> None:
    client = TestClient(create_app())
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"ok": True, "service": "control-plane"}
