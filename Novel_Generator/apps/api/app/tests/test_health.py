from app.core.config import settings


def test_health(client) -> None:
    response = client.get(f"{settings.api_prefix}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "queue_backend" in data
