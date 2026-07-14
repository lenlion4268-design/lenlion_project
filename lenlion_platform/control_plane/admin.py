from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Query, status

from control_plane.auth import verify_admin_header
from control_plane.models import (
    AdminAgentListResponse,
    AdminApprovalListResponse,
    AdminAuditEventListResponse,
)
from control_plane import store

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_admin(authorization: Annotated[str | None, Header()] = None) -> None:
    verify_admin_header(authorization)


@router.get("/agents", response_model=AdminAgentListResponse)
def list_agents(
    tenant_id: str = Query(..., description="Tenant scope for listing"),
    limit: int = Query(50, ge=1, le=200),
    cursor: str | None = Query(None),
    authorization: Annotated[str | None, Header()] = None,
) -> AdminAgentListResponse:
    _require_admin(authorization)
    items, next_cursor = store.list_agents(tenant_id=tenant_id, limit=limit, cursor=cursor)
    return AdminAgentListResponse(items=items, next_cursor=next_cursor)


@router.get("/audit-events", response_model=AdminAuditEventListResponse)
def list_audit_events(
    tenant_id: str = Query(..., description="Tenant scope for listing"),
    limit: int = Query(50, ge=1, le=200),
    cursor: str | None = Query(None),
    authorization: Annotated[str | None, Header()] = None,
) -> AdminAuditEventListResponse:
    _require_admin(authorization)
    items, next_cursor = store.list_audit_events(
        tenant_id=tenant_id,
        limit=limit,
        cursor=cursor,
    )
    return AdminAuditEventListResponse(items=items, next_cursor=next_cursor)


@router.get("/approvals", response_model=AdminApprovalListResponse)
def list_approvals(
    tenant_id: str = Query(..., description="Tenant scope for listing"),
    limit: int = Query(50, ge=1, le=200),
    cursor: str | None = Query(None),
    authorization: Annotated[str | None, Header()] = None,
) -> AdminApprovalListResponse:
    _require_admin(authorization)
    items, next_cursor = store.list_approvals(
        tenant_id=tenant_id,
        limit=limit,
        cursor=cursor,
    )
    return AdminApprovalListResponse(items=items, next_cursor=next_cursor)


@router.post("/agents/{agent_id}/revoke")
def revoke_agent_admin(
    agent_id: str,
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, str]:
    _require_admin(authorization)
    if store.get_agent(agent_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="agent not found",
        )
    store.revoke_agent(agent_id)
    return {"status": "revoked", "agent_id": agent_id}
