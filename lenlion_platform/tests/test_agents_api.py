from __future__ import annotations

import json
import socket
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from control_plane.app import create_app as create_control_plane
from control_plane.leases import RevokedTokenError, verify_agent_token
from control_plane.policies import ensure_tenant_policy
from model_gateway.app import create_app as create_model_gateway


@pytest.fixture
def cp_client() -> TestClient:
    return TestClient(create_control_plane())


def _admin_headers() -> dict[str, str]:
    return {"Authorization": "Bearer test-admin-token-32bytes-minimum"}


def test_create_enrollment_token_requires_admin(cp_client: TestClient) -> None:
    response = cp_client.post(
        "/admin/enrollment-tokens",
        json={"tenant_id": "tenant-a"},
    )
    assert response.status_code == 401


def test_create_enrollment_token_rejects_wrong_admin(cp_client: TestClient) -> None:
    response = cp_client.post(
        "/admin/enrollment-tokens",
        json={"tenant_id": "tenant-a"},
        headers={"Authorization": "Bearer wrong-token"},
    )
    assert response.status_code == 403


def test_create_enrollment_token_success(cp_client: TestClient) -> None:
    response = cp_client.post(
        "/admin/enrollment-tokens",
        json={"tenant_id": "tenant-a", "ttl_seconds": 3600},
        headers=_admin_headers(),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["tenant_id"] == "tenant-a"
    assert body["enrollment_token"]
    assert body["expires_at"] > 0


def _register_agent(cp_client: TestClient, enrollment_token: str) -> dict:
    response = cp_client.post(
        "/agents/register",
        json={
            "enrollment_token": enrollment_token,
            "name": "edge-1",
            "hostname": socket.gethostname(),
            "version": "0.5.0",
            "capabilities": {},
        },
    )
    assert response.status_code == 200
    return response.json()


def test_register_and_heartbeat_flow(cp_client: TestClient) -> None:
    token_resp = cp_client.post(
        "/admin/enrollment-tokens",
        json={"tenant_id": "tenant-b"},
        headers=_admin_headers(),
    ).json()
    reg = _register_agent(cp_client, token_resp["enrollment_token"])
    hb = cp_client.post(
        "/agents/heartbeat",
        json={
            "agent_id": reg["agent_id"],
            "node_credential": reg["node_credential"],
            "status": "idle",
        },
    )
    assert hb.status_code == 200
    body = hb.json()
    claims = verify_agent_token(body["agent_token"])
    assert claims.agent_id == reg["agent_id"]
    assert body["policy"]["allowed_models"] == ["gpt-4o-mini"]


def test_register_rejects_token_reuse(cp_client: TestClient) -> None:
    token_resp = cp_client.post(
        "/admin/enrollment-tokens",
        json={"tenant_id": "tenant-c"},
        headers=_admin_headers(),
    ).json()
    enrollment_token = token_resp["enrollment_token"]
    _register_agent(cp_client, enrollment_token)
    response = cp_client.post(
        "/agents/register",
        json={
            "enrollment_token": enrollment_token,
            "name": "edge-2",
            "hostname": "host",
            "version": "0.5.0",
        },
    )
    assert response.status_code == 403


def test_register_rejects_invalid_token(cp_client: TestClient) -> None:
    response = cp_client.post(
        "/agents/register",
        json={
            "enrollment_token": "invalid-token",
            "name": "edge",
            "hostname": "host",
            "version": "0.5.0",
        },
    )
    assert response.status_code == 403


def test_register_rejects_expired_token(cp_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from control_plane import store as store_module

    monkeypatch.setattr(store_module, "create_enrollment_token", lambda tenant_id, ttl: (
        "expired-plaintext",
        tenant_id,
        1,
    ))

    def fake_consume(_plaintext: str) -> str:
        raise ValueError("enrollment token expired")

    monkeypatch.setattr(store_module, "consume_enrollment_token", fake_consume)
    response = cp_client.post(
        "/agents/register",
        json={
            "enrollment_token": "expired-plaintext",
            "name": "edge",
            "hostname": "host",
            "version": "0.5.0",
        },
    )
    assert response.status_code == 403


def test_revoked_agent_cannot_heartbeat(cp_client: TestClient) -> None:
    token_resp = cp_client.post(
        "/admin/enrollment-tokens",
        json={"tenant_id": "tenant-d"},
        headers=_admin_headers(),
    ).json()
    reg = _register_agent(cp_client, token_resp["enrollment_token"])
    revoke = cp_client.post(
        f"/admin/agents/{reg['agent_id']}/revoke",
        headers=_admin_headers(),
    )
    assert revoke.status_code == 200
    hb = cp_client.post(
        "/agents/heartbeat",
        json={
            "agent_id": reg["agent_id"],
            "node_credential": reg["node_credential"],
        },
    )
    assert hb.status_code == 403


def test_revoke_agent_revokes_active_leases(cp_client: TestClient) -> None:
    token_resp = cp_client.post(
        "/admin/enrollment-tokens",
        json={"tenant_id": "tenant-e"},
        headers=_admin_headers(),
    ).json()
    reg = _register_agent(cp_client, token_resp["enrollment_token"])
    hb = cp_client.post(
        "/agents/heartbeat",
        json={
            "agent_id": reg["agent_id"],
            "node_credential": reg["node_credential"],
        },
    ).json()
    agent_token = hb["agent_token"]
    verify_agent_token(agent_token)

    cp_client.post(
        f"/admin/agents/{reg['agent_id']}/revoke",
        headers=_admin_headers(),
    )
    with pytest.raises(RevokedTokenError):
        verify_agent_token(agent_token)


def test_enroll_agent_writes_managed_config(
    cp_client: TestClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import sys

    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "scripts"))
    import enroll_agent as enroll_module  # noqa: E402

    token_resp = cp_client.post(
        "/admin/enrollment-tokens",
        json={"tenant_id": "tenant-f"},
        headers=_admin_headers(),
    ).json()
    hermes_home = tmp_path / ".hermes"
    hermes_home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))
    monkeypatch.setattr(
        enroll_module,
        "register",
        lambda **kwargs: _register_agent(cp_client, token_resp["enrollment_token"]),
    )

    config_path = enroll_module.write_managed_config(
        control_plane_url="http://localhost:8080",
        model_gateway_url="http://localhost:8081",
        agent_id="agent-test",
        tenant_id="tenant-f",
        node_credential="node-secret",
    )
    text = config_path.read_text(encoding="utf-8")
    assert "provider: lenlion-cloud" in text or '"provider": "lenlion-cloud"' in text
    assert "agent-test" in text
    assert "lenlion_edge" in text
    assert "control_plane_url" in text
    assert "model_gateway_url" in text
    assert "agent_token" not in text
    env_path = hermes_home / ".env"
    if env_path.exists():
        assert "agent_token" not in env_path.read_text(encoding="utf-8").lower()

    # Existing plugins must be preserved (append, not overwrite).
    cfg_path = hermes_home / "config.yaml"
    cfg_path.write_text("plugins:\n  enabled:\n    - security-guidance\n", encoding="utf-8")
    config_path = enroll_module.write_managed_config(
        control_plane_url="http://localhost:8080",
        model_gateway_url="http://localhost:8081",
        agent_id="agent-test",
        tenant_id="tenant-f",
        node_credential="node-secret",
    )
    merged = config_path.read_text(encoding="utf-8")
    assert "security-guidance" in merged
    assert "lenlion_edge" in merged


def test_hard_control_gateway_smoke(cp_client: TestClient) -> None:
    token_resp = cp_client.post(
        "/admin/enrollment-tokens",
        json={"tenant_id": "tenant-smoke"},
        headers=_admin_headers(),
    ).json()
    reg = _register_agent(cp_client, token_resp["enrollment_token"])
    hb = cp_client.post(
        "/agents/heartbeat",
        json={
            "agent_id": reg["agent_id"],
            "node_credential": reg["node_credential"],
        },
    ).json()
    agent_token = hb["agent_token"]

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/chat/completions"):
            return httpx.Response(
                200,
                json={
                    "id": "chatcmpl-test",
                    "object": "chat.completion",
                    "choices": [{"message": {"role": "assistant", "content": "ok"}}],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 2},
                },
            )
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    gw = TestClient(create_model_gateway(http_client=client))

    ok = gw.post(
        "/v1/chat/completions",
        headers={"Authorization": f"Bearer {agent_token}"},
        json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "hi"}]},
    )
    assert ok.status_code == 200

    cp_client.post(
        f"/admin/agents/{reg['agent_id']}/revoke",
        headers=_admin_headers(),
    )
    denied = gw.post(
        "/v1/chat/completions",
        headers={"Authorization": f"Bearer {agent_token}"},
        json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "hi"}]},
    )
    assert denied.status_code == 401
