"""Lenlion Edge plugin — lease cache and local defense-in-depth (Phase 3 batch 1).

Task 5 scope: heartbeat lease cache, token-provider injection, pre_tool_call
lease/hardline gating, on_session_start warm. Cloud approval (task 7) and
event upload (task 8) are intentionally not wired yet.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from hermes_cli.config import load_config

from .client import ControlPlaneClient
from .lease_cache import LeaseCache
from .protocol import LeaseUnavailableError

logger = logging.getLogger(__name__)

_TOKEN_PROVIDER_NAME = "lenlion-cloud"

_cache: LeaseCache | None = None
_client: ControlPlaneClient | None = None
_managed_enabled: bool = False


def _platform_config() -> dict[str, Any]:
    config = load_config()
    section = config.get("lenlion_platform")
    return section if isinstance(section, dict) else {}


def get_agent_token() -> str:
    """Callable api_key entrypoint for lenlion-cloud. Fail-closed."""
    if _cache is None:
        raise LeaseUnavailableError(
            "lenlion_edge: token provider not registered "
            "(plugin not loaded or managed mode disabled)"
        )
    return _cache.get_agent_token()


def _block(message: str) -> dict[str, str]:
    return {"action": "block", "message": message}


def _on_session_start(session_id: str = "", **_: Any) -> None:
    """Observer only — warm lease cache; cannot veto session start."""
    if _cache is None:
        return
    _cache.set_active_session(session_id or None)
    _cache.warm()


def _on_pre_tool_call(
    tool_name: str = "",
    args: Any = None,
    **_: Any,
) -> Optional[dict[str, str]]:
    """Decision chain (batch 1): lease → local hardline → allow.

    Cloud approval is inserted after hardline in task 7.
    """
    if not _managed_enabled or _cache is None:
        return None

    policy = _cache.policy
    high_risk = list(policy.high_risk_tools) if policy else ["terminal", "execute_code"]
    if tool_name not in high_risk:
        return None

    try:
        _cache.get_agent_token()
    except LeaseUnavailableError as exc:
        return _block(str(exc))

    args_dict = args if isinstance(args, dict) else {}
    command = str(args_dict.get("command") or args_dict.get("cmd") or "")
    if command:
        try:
            from tools.approval import detect_hardline_command

            is_hardline, hardline_desc = detect_hardline_command(command)
            if is_hardline:
                return _block(
                    f"lenlion_edge: hardline blocked locally ({hardline_desc})"
                )
        except Exception as exc:
            logger.debug("lenlion_edge: hardline check failed: %s", exc)

    return None


def register(ctx: Any) -> None:
    """Plugin entrypoint — inject token provider and register hooks."""
    global _cache, _client, _managed_enabled

    platform = _platform_config()
    _managed_enabled = bool(platform.get("enabled"))
    if not _managed_enabled:
        logger.info("lenlion_edge: managed mode disabled; hooks idle")
        return

    control_plane_url = str(
        platform.get("control_plane_url") or platform.get("base_url") or ""
    ).strip()
    agent_id = str(platform.get("agent_id") or "").strip()
    node_credential = str(platform.get("node_credential") or "").strip()
    if not control_plane_url or not agent_id or not node_credential:
        logger.error(
            "lenlion_edge: managed mode enabled but control_plane_url/agent_id/"
            "node_credential incomplete"
        )
        return

    _client = ControlPlaneClient(
        control_plane_url=control_plane_url,
        agent_id=agent_id,
        node_credential=node_credential,
    )
    _cache = LeaseCache(_client)

    from hermes_cli.runtime_provider import register_runtime_token_provider

    register_runtime_token_provider(_TOKEN_PROVIDER_NAME, get_agent_token)

    ctx.register_hook("on_session_start", _on_session_start)
    ctx.register_hook("pre_tool_call", _on_pre_tool_call)
    logger.info("lenlion_edge: registered for agent_id=%s", agent_id)


def _reset_for_tests() -> None:
    """Test helper — clear module state."""
    global _cache, _client, _managed_enabled
    if _client is not None:
        try:
            _client.close()
        except Exception:
            pass
    _cache = None
    _client = None
    _managed_enabled = False
    try:
        from hermes_cli.runtime_provider import clear_runtime_token_providers

        clear_runtime_token_providers()
    except Exception:
        pass
