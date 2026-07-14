"""In-process lease cache with proactive refresh."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any

from .client import ControlPlaneClient
from .protocol import EdgePolicy, LeaseUnavailableError

logger = logging.getLogger(__name__)

# Refresh when remaining TTL drops below this fraction of lease_ttl.
_REFRESH_FRACTION = 0.25
_MIN_REFRESH_SECONDS = 15


class LeaseCache:
    def __init__(self, client: ControlPlaneClient) -> None:
        self._client = client
        self._lock = threading.RLock()
        self._agent_token: str | None = None
        self._lease_expires_at: int = 0
        self._policy: EdgePolicy | None = None
        self._active_session_id: str | None = None

    @property
    def policy(self) -> EdgePolicy | None:
        with self._lock:
            return self._policy

    def set_active_session(self, session_id: str | None) -> None:
        with self._lock:
            self._active_session_id = session_id

    def clear(self) -> None:
        with self._lock:
            self._agent_token = None
            self._lease_expires_at = 0
            self._policy = None

    def has_valid_lease(self, *, now: int | None = None) -> bool:
        now = int(time.time() if now is None else now)
        with self._lock:
            return bool(self._agent_token) and self._lease_expires_at > now

    def get_agent_token(self, *, force_refresh: bool = False) -> str:
        """Return a valid agent_token, refreshing if needed. Fail-closed."""
        with self._lock:
            now = int(time.time())
            if (
                not force_refresh
                and self._agent_token
                and self._lease_expires_at > now
                and not self._should_refresh(now)
            ):
                return self._agent_token
            return self._refresh_locked(status="running" if self._active_session_id else "idle")

    def warm(self) -> None:
        """Best-effort cache warm used by on_session_start (observer only)."""
        try:
            self.get_agent_token()
        except Exception as exc:
            logger.warning("lenlion_edge: lease warm failed: %s", exc)

    def _should_refresh(self, now: int) -> bool:
        if not self._agent_token or self._lease_expires_at <= now:
            return True
        remaining = self._lease_expires_at - now
        ttl = self._policy.lease_ttl_seconds if self._policy else remaining
        threshold = max(_MIN_REFRESH_SECONDS, int(ttl * _REFRESH_FRACTION))
        return remaining <= threshold

    def _refresh_locked(self, *, status: str) -> str:
        try:
            result = self._client.heartbeat(
                policy_etag=self._policy.etag if self._policy else None,
                status=status,
                active_session_id=self._active_session_id,
            )
        except Exception as exc:
            self._agent_token = None
            self._lease_expires_at = 0
            raise LeaseUnavailableError(
                f"lenlion_edge: failed to refresh agent lease: {exc}"
            ) from exc

        if not result.agent_token or result.lease_expires_at <= int(time.time()):
            self._agent_token = None
            self._lease_expires_at = 0
            raise LeaseUnavailableError(
                "lenlion_edge: control plane returned an invalid lease"
            )

        self._agent_token = result.agent_token
        self._lease_expires_at = result.lease_expires_at
        self._policy = result.policy
        return self._agent_token

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "has_token": bool(self._agent_token),
                "lease_expires_at": self._lease_expires_at,
                "policy_etag": self._policy.etag if self._policy else None,
            }
