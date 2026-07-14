from __future__ import annotations

import time

from control_plane import store
from control_plane.models import EdgePolicy


def default_policy() -> EdgePolicy:
    return EdgePolicy(
        etag="default-v1",
        allowed_models=["gpt-4o-mini"],
        allowed_toolsets=["terminal", "file", "web"],
    )


def ensure_tenant_policy(tenant_id: str) -> EdgePolicy:
    policy = store.get_tenant_policy(tenant_id)
    if policy is not None:
        return policy
    policy = default_policy()
    store.upsert_tenant_policy(tenant_id, policy, updated_at=int(time.time()))
    return policy


def get_agent_policy(tenant_id: str, agent_id: str) -> EdgePolicy | None:
    agent_policy = store.get_agent_policy(tenant_id, agent_id)
    if agent_policy is not None:
        return agent_policy
    return store.get_tenant_policy(tenant_id)


def resolve_policy(
    tenant_id: str,
    agent_id: str,
    policy_etag: str,
) -> EdgePolicy | None:
    policy = get_agent_policy(tenant_id, agent_id)
    if policy is None:
        return None
    if policy.etag != policy_etag:
        return None
    return policy
