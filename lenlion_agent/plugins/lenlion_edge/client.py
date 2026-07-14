"""HTTP client for the Lenlion control plane (heartbeat for batch 1)."""

from __future__ import annotations

from typing import Any

import httpx

from .protocol import HeartbeatResult

DEFAULT_HEARTBEAT_TIMEOUT_SECONDS = 15.0


class ControlPlaneClient:
    def __init__(
        self,
        *,
        control_plane_url: str,
        agent_id: str,
        node_credential: str,
        heartbeat_timeout_seconds: float = DEFAULT_HEARTBEAT_TIMEOUT_SECONDS,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.control_plane_url = control_plane_url.rstrip("/")
        self.agent_id = agent_id
        self.node_credential = node_credential
        self.heartbeat_timeout_seconds = float(heartbeat_timeout_seconds)
        self._owns_client = http_client is None
        self._http = http_client or httpx.Client()

    def close(self) -> None:
        if self._owns_client:
            self._http.close()

    def heartbeat(
        self,
        *,
        policy_etag: str | None = None,
        status: str = "idle",
        active_session_id: str | None = None,
    ) -> HeartbeatResult:
        payload: dict[str, Any] = {
            "agent_id": self.agent_id,
            "node_credential": self.node_credential,
            "status": status,
        }
        if policy_etag:
            payload["policy_etag"] = policy_etag
        if active_session_id:
            payload["active_session_id"] = active_session_id
        response = self._http.post(
            f"{self.control_plane_url}/agents/heartbeat",
            json=payload,
            timeout=self.heartbeat_timeout_seconds,
        )
        response.raise_for_status()
        return HeartbeatResult.from_dict(response.json())
