from __future__ import annotations

import httpx
import pytest
from fastapi.testclient import TestClient

from control_plane.app import create_app as create_control_plane
from control_plane.leases import verify_agent_token
from model_gateway.app import create_app as create_model_gateway


def _bootstrap_agent(cp: TestClient) -> tuple[str, str]:
    admin = {"Authorization": "Bearer test-admin-token-32bytes-minimum"}
    token = cp.post(
        "/admin/enrollment-tokens",
        json={"tenant_id": "tenant-gw"},
        headers=admin,
    ).json()["enrollment_token"]
    reg = cp.post(
        "/agents/register",
        json={
            "enrollment_token": token,
            "name": "gw-agent",
            "hostname": "host",
            "version": "0.5.0",
        },
    ).json()
    hb = cp.post(
        "/agents/heartbeat",
        json={
            "agent_id": reg["agent_id"],
            "node_credential": reg["node_credential"],
        },
    ).json()
    return reg["agent_id"], hb["agent_token"]


def test_missing_token_returns_401() -> None:
    gw = TestClient(create_model_gateway(http_client=httpx.AsyncClient()))
    response = gw.post(
        "/v1/chat/completions",
        json={"model": "gpt-4o-mini", "messages": []},
    )
    assert response.status_code == 401


def test_revoked_token_returns_401() -> None:
    cp = TestClient(create_control_plane())
    agent_id, agent_token = _bootstrap_agent(cp)
    cp.post(
        f"/admin/agents/{agent_id}/revoke",
        headers={"Authorization": "Bearer test-admin-token-32bytes-minimum"},
    )
    gw = TestClient(create_model_gateway(http_client=httpx.AsyncClient()))
    response = gw.post(
        "/v1/chat/completions",
        headers={"Authorization": f"Bearer {agent_token}"},
        json={"model": "gpt-4o-mini", "messages": []},
    )
    assert response.status_code == 401


def test_disallowed_model_returns_403() -> None:
    cp = TestClient(create_control_plane())
    _agent_id, agent_token = _bootstrap_agent(cp)

    def handler(_request: httpx.Request) -> httpx.Response:
        raise AssertionError("upstream should not be called")

    gw = TestClient(
        create_model_gateway(http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    )
    response = gw.post(
        "/v1/chat/completions",
        headers={"Authorization": f"Bearer {agent_token}"},
        json={"model": "gpt-4o", "messages": []},
    )
    assert response.status_code == 403


def test_stale_policy_etag_returns_403(monkeypatch: pytest.MonkeyPatch) -> None:
    import model_gateway.app as gateway_app

    cp = TestClient(create_control_plane())
    _agent_id, agent_token = _bootstrap_agent(cp)

    def stale_policy(*args, **kwargs):
        return None

    monkeypatch.setattr(gateway_app, "resolve_policy", stale_policy)
    gw = TestClient(create_model_gateway(http_client=httpx.AsyncClient()))
    response = gw.post(
        "/v1/chat/completions",
        headers={"Authorization": f"Bearer {agent_token}"},
        json={"model": "gpt-4o-mini", "messages": []},
    )
    assert response.status_code == 403


def test_allowed_request_is_forwarded() -> None:
    cp = TestClient(create_control_plane())
    _agent_id, agent_token = _bootstrap_agent(cp)
    verify_agent_token(agent_token)

    seen_models: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = httpx.Request(
            request.method,
            request.url,
            content=request.content,
            headers=request.headers,
        ).read()
        import json

        body = json.loads(payload)
        seen_models.append(body["model"])
        return httpx.Response(
            200,
            json={
                "id": "chatcmpl-1",
                "object": "chat.completion",
                "choices": [{"message": {"role": "assistant", "content": "hello"}}],
                "usage": {"prompt_tokens": 3, "completion_tokens": 5},
            },
        )

    transport = httpx.MockTransport(handler)
    gw = TestClient(create_model_gateway(http_client=httpx.AsyncClient(transport=transport)))
    response = gw.post(
        "/v1/chat/completions",
        headers={"Authorization": f"Bearer {agent_token}"},
        json={
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": "hello"}],
        },
    )
    assert response.status_code == 200
    assert seen_models == ["gpt-4o-mini"]
    assert response.json()["choices"][0]["message"]["content"] == "hello"


def test_empty_allowed_models_is_deny_all() -> None:
    from control_plane import store
    from control_plane.models import EdgePolicy
    import time

    cp = TestClient(create_control_plane())
    _agent_id, agent_token = _bootstrap_agent(cp)
    store.upsert_tenant_policy(
        "tenant-gw",
        EdgePolicy(etag="default-v1", allowed_models=[]),
        updated_at=int(time.time()),
    )
    gw = TestClient(create_model_gateway(http_client=httpx.AsyncClient()))
    response = gw.post(
        "/v1/chat/completions",
        headers={"Authorization": f"Bearer {agent_token}"},
        json={"model": "gpt-4o-mini", "messages": []},
    )
    assert response.status_code == 403
