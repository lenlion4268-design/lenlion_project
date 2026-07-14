from __future__ import annotations

import socket

import pytest
from fastapi.testclient import TestClient

from control_plane.app import create_app
from control_plane import store


@pytest.fixture
def cp_client() -> TestClient:
    return TestClient(create_app())


def _admin_headers() -> dict[str, str]:
    return {"Authorization": "Bearer test-admin-token-32bytes-minimum"}


def _register_agent(cp_client: TestClient, tenant_id: str = "tenant-admin") -> dict:
    token_resp = cp_client.post(
        "/admin/enrollment-tokens",
        json={"tenant_id": tenant_id},
        headers=_admin_headers(),
    ).json()
    response = cp_client.post(
        "/agents/register",
        json={
            "enrollment_token": token_resp["enrollment_token"],
            "name": "edge-admin",
            "hostname": socket.gethostname(),
            "version": "0.6.0",
            "capabilities": {},
        },
    )
    assert response.status_code == 200
    return response.json()


def test_admin_list_requires_token(cp_client: TestClient) -> None:
    response = cp_client.get("/admin/agents", params={"tenant_id": "tenant-admin"})
    assert response.status_code == 401


def test_admin_list_agents(cp_client: TestClient) -> None:
    reg = _register_agent(cp_client)
    response = cp_client.get(
        "/admin/agents",
        params={"tenant_id": reg["tenant_id"]},
        headers=_admin_headers(),
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) >= 1
    agent = body["items"][0]
    assert agent["id"] == reg["agent_id"]
    assert agent["tenant_id"] == reg["tenant_id"]
    assert "node_credential_hash" not in agent
    assert "node_credential" not in agent


def test_admin_list_agents_tenant_isolation(cp_client: TestClient) -> None:
    reg_a = _register_agent(cp_client, tenant_id="tenant-a")
    _register_agent(cp_client, tenant_id="tenant-b")
    response = cp_client.get(
        "/admin/agents",
        params={"tenant_id": "tenant-a"},
        headers=_admin_headers(),
    )
    ids = {item["id"] for item in response.json()["items"]}
    assert reg_a["agent_id"] in ids
    assert all(item["tenant_id"] == "tenant-a" for item in response.json()["items"])


def test_admin_revoke_via_admin_router(cp_client: TestClient) -> None:
    reg = _register_agent(cp_client)
    response = cp_client.post(
        f"/admin/agents/{reg['agent_id']}/revoke",
        headers=_admin_headers(),
    )
    assert response.status_code == 200
    assert store.is_agent_revoked(reg["agent_id"])


def test_admin_audit_events(cp_client: TestClient) -> None:
    reg = _register_agent(cp_client)
    store.insert_audit_event_for_test(
        tenant_id=reg["tenant_id"],
        agent_id=reg["agent_id"],
        session_id="sess-1",
        kind="tool.complete",
        payload={"tool": "terminal"},
    )
    response = cp_client.get(
        "/admin/audit-events",
        params={"tenant_id": reg["tenant_id"]},
        headers=_admin_headers(),
    )
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) >= 1
    assert items[0]["kind"] == "tool.complete"
    assert "node_credential" not in items[0]


def test_admin_approvals(cp_client: TestClient) -> None:
    reg = _register_agent(cp_client)
    store.insert_approval_for_test(
        tenant_id=reg["tenant_id"],
        agent_id=reg["agent_id"],
        session_id="sess-1",
        tool="terminal",
        decision="deny",
        reason="blocked",
    )
    response = cp_client.get(
        "/admin/approvals",
        params={"tenant_id": reg["tenant_id"]},
        headers=_admin_headers(),
    )
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) >= 1
    assert items[0]["decision"] == "deny"
    assert "args_digest" not in items[0]
