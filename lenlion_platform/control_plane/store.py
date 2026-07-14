from __future__ import annotations

import json
import os
import time
from typing import Any

from psycopg.types.json import Jsonb

from control_plane.auth import hash_secret, new_id, new_token, verify_secret
from control_plane.db import transaction
from control_plane.models import AdminAgentRow, AdminApprovalRow, AdminAuditEventRow, EdgePolicy


def use_memory_store() -> bool:
    return os.environ.get("LENLION_PLATFORM_USE_MEMORY", "").strip() == "1"


# --- memory backend state ---

_memory: dict[str, Any] = {
    "tenants": {},
    "enrollment_tokens": {},
    "agents": {},
    "leases": {},
    "policies": {},
    "audit_events": {},
    "approvals": {},
}


def reset_memory_store() -> None:
    for key in _memory:
        if isinstance(_memory[key], dict):
            _memory[key].clear()


def _policy_key(tenant_id: str, scope: str, target_id: str) -> str:
    return f"{tenant_id}:{scope}:{target_id}"


def ensure_tenant(tenant_id: str, name: str | None = None) -> None:
    if use_memory_store():
        if tenant_id not in _memory["tenants"]:
            _memory["tenants"][tenant_id] = {
                "id": tenant_id,
                "name": name or tenant_id,
                "created_at": int(time.time()),
            }
        return
    now = int(time.time())
    with transaction() as conn:
        conn.execute(
            """
            INSERT INTO tenants (id, name, created_at)
            VALUES (%s, %s, %s)
            ON CONFLICT (id) DO NOTHING
            """,
            (tenant_id, name or tenant_id, now),
        )


def create_enrollment_token(
    tenant_id: str,
    ttl_seconds: int,
) -> tuple[str, str, int]:
    ensure_tenant(tenant_id)
    token_id = new_id("et_")
    plaintext = new_token()
    token_hash = hash_secret(plaintext)
    now = int(time.time())
    expires_at = now + ttl_seconds
    if use_memory_store():
        _memory["enrollment_tokens"][token_id] = {
            "id": token_id,
            "tenant_id": tenant_id,
            "token_hash": token_hash,
            "expires_at": expires_at,
            "used_at": None,
            "created_at": now,
        }
        return plaintext, tenant_id, expires_at
    with transaction() as conn:
        conn.execute(
            """
            INSERT INTO enrollment_tokens
                (id, tenant_id, token_hash, expires_at, created_at)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (token_id, tenant_id, token_hash, expires_at, now),
        )
    return plaintext, tenant_id, expires_at


def consume_enrollment_token(plaintext: str) -> str:
    now = int(time.time())
    if use_memory_store():
        for record in _memory["enrollment_tokens"].values():
            if not verify_secret(plaintext, record["token_hash"]):
                continue
            if record["used_at"] is not None:
                raise ValueError("enrollment token already used")
            if record["expires_at"] < now:
                raise ValueError("enrollment token expired")
            record["used_at"] = now
            return record["tenant_id"]
        raise ValueError("invalid enrollment token")
    token_hash = hash_secret(plaintext)
    with transaction() as conn:
        row = conn.execute(
            """
            SELECT id, tenant_id, expires_at, used_at
            FROM enrollment_tokens
            WHERE token_hash = %s
            FOR UPDATE
            """,
            (token_hash,),
        ).fetchone()
        if row is None:
            raise ValueError("invalid enrollment token")
        token_id, tenant_id, expires_at, used_at = row
        if used_at is not None:
            raise ValueError("enrollment token already used")
        if expires_at < now:
            raise ValueError("enrollment token expired")
        conn.execute(
            "UPDATE enrollment_tokens SET used_at = %s WHERE id = %s",
            (now, token_id),
        )
    return tenant_id


def register_agent(
    tenant_id: str,
    name: str,
    hostname: str,
    version: str,
    capabilities: dict[str, Any],
) -> tuple[str, str]:
    agent_id = new_id("agent_")
    node_credential = new_token()
    credential_hash = hash_secret(node_credential)
    now = int(time.time())
    if use_memory_store():
        _memory["agents"][agent_id] = {
            "id": agent_id,
            "tenant_id": tenant_id,
            "name": name,
            "hostname": hostname,
            "version": version,
            "node_credential_hash": credential_hash,
            "status": "idle",
            "capabilities": capabilities,
            "last_heartbeat": None,
            "revoked_at": None,
            "created_at": now,
        }
        return agent_id, node_credential
    with transaction() as conn:
        conn.execute(
            """
            INSERT INTO agents (
                id, tenant_id, name, hostname, version,
                node_credential_hash, status, capabilities, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                agent_id,
                tenant_id,
                name,
                hostname,
                version,
                credential_hash,
                "idle",
                Jsonb(capabilities),
                now,
            ),
        )
    return agent_id, node_credential


def get_agent(agent_id: str) -> dict[str, Any] | None:
    if use_memory_store():
        return _memory["agents"].get(agent_id)
    with transaction() as conn:
        row = conn.execute(
            """
            SELECT id, tenant_id, name, hostname, version, status,
                   last_heartbeat, revoked_at, created_at, node_credential_hash
            FROM agents WHERE id = %s
            """,
            (agent_id,),
        ).fetchone()
    if row is None:
        return None
    return {
        "id": row[0],
        "tenant_id": row[1],
        "name": row[2],
        "hostname": row[3],
        "version": row[4],
        "status": row[5],
        "last_heartbeat": row[6],
        "revoked_at": row[7],
        "created_at": row[8],
        "node_credential_hash": row[9],
    }


def verify_node_credential(agent_id: str, node_credential: str) -> bool:
    agent = get_agent(agent_id)
    if agent is None:
        return False
    return verify_secret(node_credential, agent["node_credential_hash"])


def is_agent_revoked(agent_id: str) -> bool:
    agent = get_agent(agent_id)
    if agent is None:
        return True
    return agent.get("revoked_at") is not None


def update_agent_heartbeat(agent_id: str, status: str) -> None:
    now = int(time.time())
    if use_memory_store():
        agent = _memory["agents"].get(agent_id)
        if agent is not None:
            agent["status"] = status
            agent["last_heartbeat"] = now
        return
    with transaction() as conn:
        conn.execute(
            "UPDATE agents SET status = %s, last_heartbeat = %s WHERE id = %s",
            (status, now, agent_id),
        )


def revoke_agent(agent_id: str) -> None:
    now = int(time.time())
    if use_memory_store():
        agent = _memory["agents"].get(agent_id)
        if agent is not None:
            agent["revoked_at"] = now
        for lease in _memory["leases"].values():
            if lease["agent_id"] == agent_id and lease["revoked_at"] is None:
                lease["revoked_at"] = now
        return
    with transaction() as conn:
        conn.execute(
            "UPDATE agents SET revoked_at = %s WHERE id = %s",
            (now, agent_id),
        )
        conn.execute(
            """
            UPDATE leases SET revoked_at = %s
            WHERE agent_id = %s AND revoked_at IS NULL
            """,
            (now, agent_id),
        )


def insert_lease(
    *,
    jti: str,
    tenant_id: str,
    agent_id: str,
    policy_etag: str,
    issued_at: int,
    expires_at: int,
) -> None:
    if use_memory_store():
        _memory["leases"][jti] = {
            "jti": jti,
            "tenant_id": tenant_id,
            "agent_id": agent_id,
            "policy_etag": policy_etag,
            "issued_at": issued_at,
            "expires_at": expires_at,
            "revoked_at": None,
        }
        return
    with transaction() as conn:
        conn.execute(
            """
            INSERT INTO leases
                (jti, tenant_id, agent_id, policy_etag, issued_at, expires_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (jti, tenant_id, agent_id, policy_etag, issued_at, expires_at),
        )


def is_lease_revoked(jti: str) -> bool:
    if use_memory_store():
        lease = _memory["leases"].get(jti)
        if lease is None:
            return True
        return lease.get("revoked_at") is not None
    with transaction() as conn:
        row = conn.execute(
            "SELECT revoked_at FROM leases WHERE jti = %s",
            (jti,),
        ).fetchone()
    if row is None:
        return True
    return row[0] is not None


def revoke_lease(jti: str) -> None:
    now = int(time.time())
    if use_memory_store():
        lease = _memory["leases"].get(jti)
        if lease is not None:
            lease["revoked_at"] = now
        return
    with transaction() as conn:
        conn.execute(
            "UPDATE leases SET revoked_at = %s WHERE jti = %s",
            (now, jti),
        )


def _edge_policy_from_row(policy_json: Any, etag: str) -> EdgePolicy:
    if isinstance(policy_json, str):
        data = json.loads(policy_json)
    else:
        data = dict(policy_json)
    data["etag"] = etag
    return EdgePolicy.model_validate(data)


def upsert_tenant_policy(tenant_id: str, policy: EdgePolicy, updated_at: int) -> None:
    policy_id = new_id("pol_")
    payload = policy.model_dump()
    etag = payload.pop("etag")
    if use_memory_store():
        key = _policy_key(tenant_id, "tenant", tenant_id)
        _memory["policies"][key] = {
            "id": policy_id,
            "tenant_id": tenant_id,
            "scope": "tenant",
            "target_id": tenant_id,
            "etag": etag,
            "policy": payload,
            "updated_at": updated_at,
        }
        return
    with transaction() as conn:
        conn.execute(
            """
            INSERT INTO policies
                (id, tenant_id, scope, target_id, etag, policy, updated_at)
            VALUES (%s, %s, 'tenant', %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            """,
            (policy_id, tenant_id, tenant_id, etag, Jsonb(payload), updated_at),
        )


def get_tenant_policy(tenant_id: str) -> EdgePolicy | None:
    return _get_policy(tenant_id, "tenant", tenant_id)


def get_agent_policy(tenant_id: str, agent_id: str) -> EdgePolicy | None:
    return _get_policy(tenant_id, "agent", agent_id)


def _get_policy(tenant_id: str, scope: str, target_id: str) -> EdgePolicy | None:
    if use_memory_store():
        key = _policy_key(tenant_id, scope, target_id)
        record = _memory["policies"].get(key)
        if record is None:
            return None
        return _edge_policy_from_row(record["policy"], record["etag"])
    with transaction() as conn:
        row = conn.execute(
            """
            SELECT etag, policy FROM policies
            WHERE tenant_id = %s AND scope = %s AND target_id = %s
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            (tenant_id, scope, target_id),
        ).fetchone()
    if row is None:
        return None
    return _edge_policy_from_row(row[1], row[0])


def record_model_usage(
    *,
    tenant_id: str,
    agent_id: str,
    session_id: str | None,
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> None:
    now = int(time.time())
    if use_memory_store():
        return
    with transaction() as conn:
        conn.execute(
            """
            INSERT INTO model_usage (
                tenant_id, agent_id, session_id, provider, model,
                input_tokens, output_tokens, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                tenant_id,
                agent_id,
                session_id,
                provider,
                model,
                input_tokens,
                output_tokens,
                now,
            ),
        )


def _parse_cursor(cursor: str | None) -> int:
    if not cursor:
        return 0
    try:
        return max(int(cursor), 0)
    except ValueError:
        return 0


def _agent_row_from_record(record: dict[str, Any]) -> AdminAgentRow:
    return AdminAgentRow(
        id=record["id"],
        tenant_id=record["tenant_id"],
        name=record["name"],
        hostname=record["hostname"],
        version=record["version"],
        status=record["status"],
        last_heartbeat=record.get("last_heartbeat"),
        revoked_at=record.get("revoked_at"),
        created_at=record["created_at"],
    )


def list_agents(
    *,
    tenant_id: str,
    limit: int,
    cursor: str | None,
) -> tuple[list[AdminAgentRow], str | None]:
    offset = _parse_cursor(cursor)
    if use_memory_store():
        rows = [
            _agent_row_from_record(agent)
            for agent in _memory["agents"].values()
            if agent["tenant_id"] == tenant_id
        ]
        rows.sort(key=lambda row: row.created_at, reverse=True)
        page = rows[offset : offset + limit]
        next_offset = offset + limit
        next_cursor = str(next_offset) if next_offset < len(rows) else None
        return page, next_cursor

    with transaction() as conn:
        db_rows = conn.execute(
            """
            SELECT id, tenant_id, name, hostname, version, status,
                   last_heartbeat, revoked_at, created_at
            FROM agents
            WHERE tenant_id = %s
            ORDER BY created_at DESC
            OFFSET %s LIMIT %s
            """,
            (tenant_id, offset, limit + 1),
        ).fetchall()
    items = [
        AdminAgentRow(
            id=row[0],
            tenant_id=row[1],
            name=row[2],
            hostname=row[3],
            version=row[4],
            status=row[5],
            last_heartbeat=row[6],
            revoked_at=row[7],
            created_at=row[8],
        )
        for row in db_rows[:limit]
    ]
    next_cursor = str(offset + limit) if len(db_rows) > limit else None
    return items, next_cursor


def insert_audit_event(
    *,
    tenant_id: str,
    agent_id: str | None,
    session_id: str | None,
    kind: str,
    payload: dict[str, Any] | None = None,
    created_at: int | None = None,
) -> str:
    event_id = new_id("ae_")
    now = created_at or int(time.time())
    record = {
        "id": event_id,
        "tenant_id": tenant_id,
        "agent_id": agent_id,
        "session_id": session_id,
        "kind": kind,
        "payload": payload or {},
        "created_at": now,
    }
    if use_memory_store():
        _memory["audit_events"][event_id] = record
        return event_id
    with transaction() as conn:
        row = conn.execute(
            """
            INSERT INTO audit_events
                (tenant_id, agent_id, session_id, kind, payload, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                tenant_id,
                agent_id,
                session_id,
                kind,
                Jsonb(payload or {}),
                now,
            ),
        ).fetchone()
    return str(row[0])


def insert_audit_event_for_test(
    *,
    tenant_id: str,
    agent_id: str | None,
    session_id: str | None,
    kind: str,
    payload: dict[str, Any] | None = None,
    created_at: int | None = None,
) -> str:
    return insert_audit_event(
        tenant_id=tenant_id,
        agent_id=agent_id,
        session_id=session_id,
        kind=kind,
        payload=payload,
        created_at=created_at,
    )


def list_audit_events(
    *,
    tenant_id: str,
    limit: int,
    cursor: str | None,
) -> tuple[list[AdminAuditEventRow], str | None]:
    offset = _parse_cursor(cursor)
    if use_memory_store():
        rows = [
            AdminAuditEventRow(
                id=record["id"],
                tenant_id=record["tenant_id"],
                agent_id=record.get("agent_id"),
                session_id=record.get("session_id"),
                kind=record["kind"],
                payload=dict(record.get("payload") or {}),
                created_at=record["created_at"],
            )
            for record in _memory["audit_events"].values()
            if record["tenant_id"] == tenant_id
        ]
        rows.sort(key=lambda row: row.created_at, reverse=True)
        page = rows[offset : offset + limit]
        next_offset = offset + limit
        next_cursor = str(next_offset) if next_offset < len(rows) else None
        return page, next_cursor

    with transaction() as conn:
        db_rows = conn.execute(
            """
            SELECT id, tenant_id, agent_id, session_id, kind, payload, created_at
            FROM audit_events
            WHERE tenant_id = %s
            ORDER BY created_at DESC
            OFFSET %s LIMIT %s
            """,
            (tenant_id, offset, limit + 1),
        ).fetchall()
    items = [
        AdminAuditEventRow(
            id=str(row[0]),
            tenant_id=row[1],
            agent_id=row[2],
            session_id=row[3],
            kind=row[4],
            payload=dict(row[5] or {}),
            created_at=row[6],
        )
        for row in db_rows[:limit]
    ]
    next_cursor = str(offset + limit) if len(db_rows) > limit else None
    return items, next_cursor


def insert_approval(
    *,
    tenant_id: str,
    agent_id: str,
    session_id: str,
    tool: str,
    args_digest: str,
    decision: str = "allow",
    decided_by: str = "policy",
    reason: str = "ok",
    approval_token_jti: str | None = None,
    created_at: int | None = None,
) -> str:
    approval_id = new_id("ap_")
    now = created_at or int(time.time())
    record = {
        "id": approval_id,
        "tenant_id": tenant_id,
        "agent_id": agent_id,
        "session_id": session_id,
        "tool": tool,
        "args_digest": args_digest,
        "decision": decision,
        "decided_by": decided_by,
        "approval_token_jti": approval_token_jti,
        "reason": reason,
        "created_at": now,
        "consumed_at": None,
    }
    if use_memory_store():
        _memory["approvals"][approval_id] = record
        return approval_id
    with transaction() as conn:
        conn.execute(
            """
            INSERT INTO approvals (
                id, tenant_id, agent_id, session_id, tool, args_digest,
                decision, decided_by, approval_token_jti, reason, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                approval_id,
                tenant_id,
                agent_id,
                session_id,
                tool,
                args_digest,
                decision,
                decided_by,
                approval_token_jti,
                reason,
                now,
            ),
        )
    return approval_id


def insert_approval_for_test(
    *,
    tenant_id: str,
    agent_id: str,
    session_id: str,
    tool: str,
    decision: str = "allow",
    decided_by: str = "policy",
    reason: str = "ok",
    created_at: int | None = None,
) -> str:
    return insert_approval(
        tenant_id=tenant_id,
        agent_id=agent_id,
        session_id=session_id,
        tool=tool,
        args_digest="test",
        decision=decision,
        decided_by=decided_by,
        reason=reason,
        created_at=created_at,
    )


def list_approvals(
    *,
    tenant_id: str,
    limit: int,
    cursor: str | None,
) -> tuple[list[AdminApprovalRow], str | None]:
    offset = _parse_cursor(cursor)
    if use_memory_store():
        rows = [
            AdminApprovalRow(
                id=record["id"],
                tenant_id=record["tenant_id"],
                agent_id=record["agent_id"],
                session_id=record["session_id"],
                tool=record["tool"],
                decision=record["decision"],
                decided_by=record["decided_by"],
                reason=record["reason"],
                created_at=record["created_at"],
                consumed_at=record.get("consumed_at"),
            )
            for record in _memory["approvals"].values()
            if record["tenant_id"] == tenant_id
        ]
        rows.sort(key=lambda row: row.created_at, reverse=True)
        page = rows[offset : offset + limit]
        next_offset = offset + limit
        next_cursor = str(next_offset) if next_offset < len(rows) else None
        return page, next_cursor

    with transaction() as conn:
        db_rows = conn.execute(
            """
            SELECT id, tenant_id, agent_id, session_id, tool, decision,
                   decided_by, reason, created_at, consumed_at
            FROM approvals
            WHERE tenant_id = %s
            ORDER BY created_at DESC
            OFFSET %s LIMIT %s
            """,
            (tenant_id, offset, limit + 1),
        ).fetchall()
    items = [
        AdminApprovalRow(
            id=row[0],
            tenant_id=row[1],
            agent_id=row[2],
            session_id=row[3],
            tool=row[4],
            decision=row[5],
            decided_by=row[6],
            reason=row[7],
            created_at=row[8],
            consumed_at=row[9],
        )
        for row in db_rows[:limit]
    ]
    next_cursor = str(offset + limit) if len(db_rows) > limit else None
    return items, next_cursor
