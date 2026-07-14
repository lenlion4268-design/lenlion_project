from __future__ import annotations

import time

import jwt
import pytest

from control_plane import store
from control_plane.leases import (
    ExpiredTokenError,
    InvalidTokenError,
    RevokedTokenError,
    AgentTokenClaims,
    get_jwt_secret,
    issue_agent_token,
    revoke_lease,
    verify_agent_token,
)


def test_issue_and_verify_agent_token() -> None:
    token, jti, exp = issue_agent_token(
        tenant_id="tenant-1",
        agent_id="agent-1",
        policy_etag="etag-1",
        ttl_seconds=600,
    )
    claims = verify_agent_token(token)
    assert claims.tenant_id == "tenant-1"
    assert claims.agent_id == "agent-1"
    assert claims.jti == jti
    assert claims.policy_etag == "etag-1"
    assert claims.exp == exp


def test_expired_token_rejected() -> None:
    payload = {
        "tenant_id": "tenant-1",
        "agent_id": "agent-1",
        "jti": "expired-jti",
        "policy_etag": "etag-1",
        "iat": int(time.time()) - 1000,
        "exp": int(time.time()) - 10,
    }
    store.insert_lease(
        jti="expired-jti",
        tenant_id="tenant-1",
        agent_id="agent-1",
        policy_etag="etag-1",
        issued_at=payload["iat"],
        expires_at=payload["exp"],
    )
    token = jwt.encode(payload, get_jwt_secret(), algorithm="HS256")
    with pytest.raises(ExpiredTokenError):
        verify_agent_token(token)


def test_revoked_jti_rejected() -> None:
    token, jti, _exp = issue_agent_token(
        tenant_id="tenant-1",
        agent_id="agent-1",
        policy_etag="etag-1",
        ttl_seconds=600,
    )
    revoke_lease(jti)
    with pytest.raises(RevokedTokenError):
        verify_agent_token(token)


def test_malformed_token_rejected() -> None:
    with pytest.raises(InvalidTokenError):
        verify_agent_token("not-a-jwt")


def test_platform_jwt_secret_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PLATFORM_JWT_SECRET", raising=False)
    with pytest.raises(RuntimeError, match="PLATFORM_JWT_SECRET"):
        get_jwt_secret()


def test_agent_token_claims_shape() -> None:
    claims = AgentTokenClaims(
        tenant_id="t",
        agent_id="a",
        jti="j",
        policy_etag="e",
        iat=1,
        exp=2,
    )
    assert claims.policy_etag == "e"
