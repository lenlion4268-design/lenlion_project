from __future__ import annotations

from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, status

from control_plane import store
from control_plane.auth import verify_admin_header
from control_plane.leases import (
    ExpiredTokenError,
    InvalidTokenError,
    RevokedTokenError,
    issue_agent_token,
)
from control_plane.models import (
    CreateEnrollmentTokenRequest,
    CreateEnrollmentTokenResponse,
    EnrollmentRequest,
    EnrollmentResponse,
    HeartbeatRequest,
    HeartbeatResponse,
)
from control_plane.policies import ensure_tenant_policy, get_agent_policy


def create_app() -> FastAPI:
    app = FastAPI(title="lenlion-control-plane")

    @app.get("/healthz")
    def healthz() -> dict[str, str | bool]:
        return {"ok": True, "service": "control-plane"}

    @app.post("/admin/enrollment-tokens", response_model=CreateEnrollmentTokenResponse)
    def create_enrollment_token(
        body: CreateEnrollmentTokenRequest,
        authorization: Annotated[str | None, Header()] = None,
    ) -> CreateEnrollmentTokenResponse:
        verify_admin_header(authorization)
        ensure_tenant_policy(body.tenant_id)
        plaintext, tenant_id, expires_at = store.create_enrollment_token(
            body.tenant_id,
            body.ttl_seconds,
        )
        return CreateEnrollmentTokenResponse(
            enrollment_token=plaintext,
            tenant_id=tenant_id,
            expires_at=expires_at,
        )

    @app.post("/agents/register", response_model=EnrollmentResponse)
    def register_agent(body: EnrollmentRequest) -> EnrollmentResponse:
        try:
            tenant_id = store.consume_enrollment_token(body.enrollment_token)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(exc),
            ) from exc
        agent_id, node_credential = store.register_agent(
            tenant_id=tenant_id,
            name=body.name,
            hostname=body.hostname,
            version=body.version,
            capabilities=body.capabilities,
        )
        return EnrollmentResponse(
            agent_id=agent_id,
            tenant_id=tenant_id,
            node_credential=node_credential,
        )

    @app.post("/agents/heartbeat", response_model=HeartbeatResponse)
    def heartbeat(body: HeartbeatRequest) -> HeartbeatResponse:
        if store.is_agent_revoked(body.agent_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="agent revoked",
            )
        if not store.verify_node_credential(body.agent_id, body.node_credential):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="invalid node credential",
            )
        agent = store.get_agent(body.agent_id)
        if agent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="agent not found",
            )
        tenant_id = agent["tenant_id"]
        policy = get_agent_policy(tenant_id, body.agent_id)
        if policy is None:
            policy = ensure_tenant_policy(tenant_id)
        store.update_agent_heartbeat(body.agent_id, body.status)
        token, _jti, expires_at = issue_agent_token(
            tenant_id=tenant_id,
            agent_id=body.agent_id,
            policy_etag=policy.etag,
            ttl_seconds=policy.lease_ttl_seconds,
        )
        return HeartbeatResponse(
            agent_token=token,
            lease_expires_at=expires_at,
            policy=policy,
        )

    @app.post("/admin/agents/{agent_id}/revoke")
    def revoke_agent(
        agent_id: str,
        authorization: Annotated[str | None, Header()] = None,
    ) -> dict[str, str]:
        verify_admin_header(authorization)
        if store.get_agent(agent_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="agent not found",
            )
        store.revoke_agent(agent_id)
        return {"status": "revoked", "agent_id": agent_id}

    return app


def gateway_auth_error(exc: Exception) -> HTTPException:
    if isinstance(exc, RevokedTokenError):
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    if isinstance(exc, ExpiredTokenError):
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    if isinstance(exc, InvalidTokenError):
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized")
