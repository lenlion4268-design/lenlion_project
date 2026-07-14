"""Minimal protocol types mirroring the control-plane Edge contract."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass(frozen=True)
class EdgePolicy:
    etag: str
    allowed_models: list[str] = field(default_factory=list)
    allowed_toolsets: list[str] = field(default_factory=list)
    high_risk_tools: list[str] = field(
        default_factory=lambda: ["terminal", "execute_code"]
    )
    approval_mode: Literal["allow_low_risk", "deny_all"] = "allow_low_risk"
    approval_timeout_seconds: int = 300
    lease_ttl_seconds: int = 600

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EdgePolicy":
        return cls(
            etag=str(data.get("etag") or ""),
            allowed_models=list(data.get("allowed_models") or []),
            allowed_toolsets=list(data.get("allowed_toolsets") or []),
            high_risk_tools=list(
                data.get("high_risk_tools") or ["terminal", "execute_code"]
            ),
            approval_mode=data.get("approval_mode") or "allow_low_risk",
            approval_timeout_seconds=int(data.get("approval_timeout_seconds") or 300),
            lease_ttl_seconds=int(data.get("lease_ttl_seconds") or 600),
        )


@dataclass(frozen=True)
class HeartbeatResult:
    agent_token: str
    lease_expires_at: int
    policy: EdgePolicy

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HeartbeatResult":
        policy_raw = data.get("policy") or {}
        if not isinstance(policy_raw, dict):
            policy_raw = {}
        return cls(
            agent_token=str(data.get("agent_token") or ""),
            lease_expires_at=int(data.get("lease_expires_at") or 0),
            policy=EdgePolicy.from_dict(policy_raw),
        )


class LeaseUnavailableError(RuntimeError):
    """Raised when no valid agent lease/token is available (fail-closed)."""
