from __future__ import annotations

import os
import time
import uuid

import jwt
from pydantic import BaseModel

from control_plane import store


class AgentTokenClaims(BaseModel):
    tenant_id: str
    agent_id: str
    jti: str
    policy_etag: str
    iat: int
    exp: int


class LeaseError(Exception):
    """Base lease validation error."""


class ExpiredTokenError(LeaseError):
    pass


class RevokedTokenError(LeaseError):
    pass


class InvalidTokenError(LeaseError):
    pass


def get_jwt_secret() -> str:
    secret = os.environ.get("PLATFORM_JWT_SECRET", "").strip()
    if not secret:
        raise RuntimeError("PLATFORM_JWT_SECRET is required")
    return secret


def issue_agent_token(
    tenant_id: str,
    agent_id: str,
    policy_etag: str,
    ttl_seconds: int,
) -> tuple[str, str, int]:
    jti = uuid.uuid4().hex
    now = int(time.time())
    exp = now + ttl_seconds
    payload = {
        "tenant_id": tenant_id,
        "agent_id": agent_id,
        "jti": jti,
        "policy_etag": policy_etag,
        "iat": now,
        "exp": exp,
    }
    token = jwt.encode(payload, get_jwt_secret(), algorithm="HS256")
    store.insert_lease(
        jti=jti,
        tenant_id=tenant_id,
        agent_id=agent_id,
        policy_etag=policy_etag,
        issued_at=now,
        expires_at=exp,
    )
    return token, jti, exp


def verify_agent_token(token: str) -> AgentTokenClaims:
    try:
        payload = jwt.decode(
            token,
            get_jwt_secret(),
            algorithms=["HS256"],
        )
    except jwt.ExpiredSignatureError as exc:
        raise ExpiredTokenError("token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise InvalidTokenError("invalid token") from exc

    claims = AgentTokenClaims.model_validate(payload)
    if store.is_lease_revoked(claims.jti):
        raise RevokedTokenError("token revoked")
    return claims


def revoke_lease(jti: str) -> None:
    store.revoke_lease(jti)
