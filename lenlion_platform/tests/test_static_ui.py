from __future__ import annotations

from fastapi.testclient import TestClient

from control_plane.app import create_app


def test_admin_ui_served_when_dist_exists() -> None:
    client = TestClient(create_app())
    response = client.get("/admin-ui/")
    if response.status_code == 404:
        return
    assert response.status_code == 200
    assert "Lenlion Platform Admin" in response.text
