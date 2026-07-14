from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class EnrollmentRequest(BaseModel):
    enrollment_token: str
    name: str
    hostname: str
    version: str
    capabilities: dict[str, Any] = Field(default_factory=dict)


class EnrollmentResponse(BaseModel):
    agent_id: str
    tenant_id: str
    node_credential: str


class CreateEnrollmentTokenRequest(BaseModel):
    tenant_id: str
    ttl_seconds: int = 3600
    name: str | None = None


class CreateEnrollmentTokenResponse(BaseModel):
    enrollment_token: str
    tenant_id: str
    expires_at: int


class HeartbeatRequest(BaseModel):
    agent_id: str
    node_credential: str
    policy_etag: str | None = None
    status: Literal["starting", "idle", "running", "paused"] = "idle"
    active_session_id: str | None = None


class EdgePolicy(BaseModel):
    etag: str
    allowed_models: list[str] = Field(default_factory=list)
    allowed_toolsets: list[str] = Field(default_factory=list)
    high_risk_tools: list[str] = Field(default_factory=lambda: ["terminal", "execute_code"])
    approval_mode: Literal["allow_low_risk", "deny_all"] = "allow_low_risk"
    approval_timeout_seconds: int = 300
    lease_ttl_seconds: int = 600


class HeartbeatResponse(BaseModel):
    agent_token: str
    lease_expires_at: int
    policy: EdgePolicy


class ApprovalRequest(BaseModel):
    agent_id: str
    session_id: str
    tool: str
    args_digest: str
    preview: str
    risk: str


class ApprovalResponse(BaseModel):
    decision: Literal["allow", "deny"]
    approval_token: str | None = None
    approval_token_jti: str | None = None
    decided_by: Literal["policy", "supervisor", "human", "timeout"]
    ttl_seconds: int = 120
    reason: str


class AuditEvent(BaseModel):
    agent_id: str
    session_id: str | None = None
    kind: str
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: int


class AdminAgentRow(BaseModel):
    id: str
    tenant_id: str
    name: str
    hostname: str
    version: str
    status: str
    last_heartbeat: int | None = None
    revoked_at: int | None = None
    created_at: int


class AdminAuditEventRow(BaseModel):
    id: str
    tenant_id: str
    agent_id: str | None = None
    session_id: str | None = None
    kind: str
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: int


class AdminApprovalRow(BaseModel):
    id: str
    tenant_id: str
    agent_id: str
    session_id: str
    tool: str
    decision: str
    decided_by: str
    reason: str
    created_at: int
    consumed_at: int | None = None


class AdminAgentListResponse(BaseModel):
    items: list[AdminAgentRow]
    next_cursor: str | None = None


class AdminAuditEventListResponse(BaseModel):
    items: list[AdminAuditEventRow]
    next_cursor: str | None = None


class AdminApprovalListResponse(BaseModel):
    items: list[AdminApprovalRow]
    next_cursor: str | None = None
