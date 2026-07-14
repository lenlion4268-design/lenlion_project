#!/usr/bin/env python3
"""Register a local Lenlion agent with the platform control plane."""

from __future__ import annotations

import argparse
import json
import os
import socket
import sys
from pathlib import Path
from typing import Any

import httpx

DEFAULT_CONTROL_PLANE_URL = "http://127.0.0.1:8080"
DEFAULT_MODEL_GATEWAY_URL = "http://127.0.0.1:8081"


def get_hermes_home() -> Path:
    return Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))


def _ensure_plugin_enabled(config: dict[str, Any], plugin_name: str) -> None:
    """Append *plugin_name* to plugins.enabled without wiping other entries."""
    plugins = config.setdefault("plugins", {})
    enabled = plugins.get("enabled")
    if not isinstance(enabled, list):
        enabled = []
    else:
        enabled = list(enabled)
    if plugin_name not in enabled:
        enabled.append(plugin_name)
    plugins["enabled"] = enabled


def write_managed_config(
    *,
    control_plane_url: str,
    model_gateway_url: str,
    agent_id: str,
    tenant_id: str,
    node_credential: str,
) -> Path:
    home = get_hermes_home()
    home.mkdir(parents=True, exist_ok=True)
    config_path = home / "config.yaml"
    config: dict[str, Any] = {}
    if config_path.exists():
        try:
            import yaml  # type: ignore

            config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        except Exception:
            config = json.loads(config_path.read_text(encoding="utf-8"))
    config.setdefault("model", {})["provider"] = "lenlion-cloud"
    config["lenlion_platform"] = {
        "enabled": True,
        "control_plane_url": control_plane_url.rstrip("/"),
        "model_gateway_url": model_gateway_url.rstrip("/"),
        # Deprecated alias kept for older edge builds that still read base_url.
        "base_url": control_plane_url.rstrip("/"),
        "agent_id": agent_id,
        "tenant_id": tenant_id,
        "node_credential": node_credential,
        "heartbeat_interval_seconds": 30,
        "approval_client_timeout_seconds": 30,
    }
    _ensure_plugin_enabled(config, "lenlion_edge")
    try:
        import yaml  # type: ignore

        config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    except ImportError:
        config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return config_path


def register(
    *,
    control_plane_url: str,
    enrollment_token: str,
    name: str,
    hostname: str,
    version: str,
    capabilities: dict[str, Any] | None = None,
) -> dict[str, Any]:
    response = httpx.post(
        f"{control_plane_url.rstrip('/')}/agents/register",
        json={
            "enrollment_token": enrollment_token,
            "name": name,
            "hostname": hostname,
            "version": version,
            "capabilities": capabilities or {},
        },
        timeout=30.0,
    )
    response.raise_for_status()
    return response.json()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Enroll a local Lenlion agent")
    parser.add_argument(
        "--control-plane-url",
        default=None,
        help=f"Control plane base URL (default: {DEFAULT_CONTROL_PLANE_URL})",
    )
    parser.add_argument(
        "--model-gateway-url",
        default=DEFAULT_MODEL_GATEWAY_URL,
        help=f"Model gateway base URL (default: {DEFAULT_MODEL_GATEWAY_URL})",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="Deprecated alias for --control-plane-url",
    )
    parser.add_argument("--name", required=True)
    parser.add_argument("--enrollment-token", required=True)
    parser.add_argument("--version", default="0.5.0")
    args = parser.parse_args(argv)

    control_plane_url = (
        args.control_plane_url
        or args.base_url
        or DEFAULT_CONTROL_PLANE_URL
    )
    model_gateway_url = args.model_gateway_url or DEFAULT_MODEL_GATEWAY_URL

    payload = register(
        control_plane_url=control_plane_url,
        enrollment_token=args.enrollment_token,
        name=args.name,
        hostname=socket.gethostname(),
        version=args.version,
    )
    config_path = write_managed_config(
        control_plane_url=control_plane_url,
        model_gateway_url=model_gateway_url,
        agent_id=payload["agent_id"],
        tenant_id=payload["tenant_id"],
        node_credential=payload["node_credential"],
    )
    print(f"Registered agent {payload['agent_id']} for tenant {payload['tenant_id']}")
    print(f"Wrote managed config to {config_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
