from __future__ import annotations

import re
from pathlib import Path

import pytest
from pydantic import ValidationError

from control_plane import db
from control_plane.models import (
    ApprovalRequest,
    ApprovalResponse,
    AuditEvent,
    CreateEnrollmentTokenRequest,
    CreateEnrollmentTokenResponse,
    EdgePolicy,
    EnrollmentRequest,
    EnrollmentResponse,
    HeartbeatRequest,
    HeartbeatResponse,
)

INIT_SQL = Path(__file__).resolve().parents[1] / "db" / "init.sql"
AGENT_OWNED_TABLES = (
    "sessions",
    "messages",
    "platform_config",
    "platform_secrets",
)


def test_get_database_url_missing_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="DATABASE_URL is required"):
        db.get_database_url()


def test_get_database_url_strips_whitespace(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "  postgresql://user:pass@localhost/db  ")
    assert db.get_database_url() == "postgresql://user:pass@localhost/db"


def test_platform_init_sql_does_not_redefine_agent_tables() -> None:
    sql = INIT_SQL.read_text(encoding="utf-8")
    for table in AGENT_OWNED_TABLES:
        pattern = rf"CREATE TABLE IF NOT EXISTS {table}\b"
        assert re.search(pattern, sql) is None, (
            f"platform init.sql must not redefine agent-owned table {table!r}"
        )


def test_platform_init_sql_uses_platform_schema_version() -> None:
    sql = INIT_SQL.read_text(encoding="utf-8")
    assert "platform_schema_version" in sql
    assert re.search(r"CREATE TABLE IF NOT EXISTS schema_version\b", sql) is None


def test_enrollment_models_minimal_payload() -> None:
    req = EnrollmentRequest(
        enrollment_token="tok",
        name="edge-1",
        hostname="host",
        version="0.1.0",
    )
    assert req.capabilities == {}
    resp = EnrollmentResponse(
        agent_id="agent-1",
        tenant_id="tenant-1",
        node_credential="cred",
    )
    assert resp.agent_id == "agent-1"


def test_create_enrollment_token_models_minimal_payload() -> None:
    req = CreateEnrollmentTokenRequest(tenant_id="tenant-1")
    assert req.ttl_seconds == 3600
    resp = CreateEnrollmentTokenResponse(
        enrollment_token="enroll-tok",
        tenant_id="tenant-1",
        expires_at=1_700_000_000,
    )
    assert resp.enrollment_token == "enroll-tok"


def test_heartbeat_models_minimal_payload() -> None:
    req = HeartbeatRequest(agent_id="agent-1", node_credential="cred")
    assert req.status == "idle"
    policy = EdgePolicy(etag="etag-1")
    resp = HeartbeatResponse(
        agent_token="lease-tok",
        lease_expires_at=1_700_000_600,
        policy=policy,
    )
    assert resp.policy.high_risk_tools == ["terminal", "execute_code"]


def test_approval_models_minimal_payload() -> None:
    req = ApprovalRequest(
        agent_id="agent-1",
        session_id="sess-1",
        tool="terminal",
        args_digest="abc",
        preview="rm -rf /",
        risk="high",
    )
    resp = ApprovalResponse(decision="allow", decided_by="policy", reason="ok")
    assert resp.ttl_seconds == 120


def test_audit_event_minimal_payload() -> None:
    event = AuditEvent(
        agent_id="agent-1",
        kind="tool_call",
        created_at=1_700_000_000,
    )
    assert event.payload == {}
    assert event.session_id is None


def test_heartbeat_request_rejects_invalid_status() -> None:
    with pytest.raises(ValidationError):
        HeartbeatRequest(
            agent_id="agent-1",
            node_credential="cred",
            status="offline",  # type: ignore[arg-type]
        )


def test_approval_response_rejects_invalid_decision() -> None:
    with pytest.raises(ValidationError):
        ApprovalResponse(
            decision="maybe",  # type: ignore[arg-type]
            decided_by="policy",
            reason="n/a",
        )
