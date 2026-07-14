"""Tests for lenlion_edge plugin (Phase 3 task 5)."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
import yaml

from hermes_cli.plugins import PluginManager


@pytest.fixture(autouse=True)
def _reset_edge():
    from plugins import lenlion_edge

    lenlion_edge._reset_for_tests()
    yield
    lenlion_edge._reset_for_tests()


def _policy_dict(**overrides: Any) -> dict[str, Any]:
    data = {
        "etag": "etag-1",
        "allowed_models": ["gpt-4o-mini"],
        "allowed_toolsets": [],
        "high_risk_tools": ["terminal", "execute_code"],
        "approval_mode": "allow_low_risk",
        "approval_timeout_seconds": 300,
        "lease_ttl_seconds": 600,
    }
    data.update(overrides)
    return data


def _heartbeat(token: str = "tok-abc", expires_in: int = 600, **policy_kw: Any) -> Any:
    from plugins.lenlion_edge.protocol import HeartbeatResult

    return HeartbeatResult.from_dict(
        {
            "agent_token": token,
            "lease_expires_at": int(time.time()) + expires_in,
            "policy": _policy_dict(**policy_kw),
        }
    )


def _write_managed_config(hermes_home: Path, **extra: Any) -> None:
    cfg = {
        "model": {"provider": "lenlion-cloud"},
        "plugins": {"enabled": ["lenlion_edge"]},
        "lenlion_platform": {
            "enabled": True,
            "control_plane_url": "http://127.0.0.1:8080",
            "model_gateway_url": "http://127.0.0.1:8081",
            "agent_id": "agent-1",
            "tenant_id": "tenant-1",
            "node_credential": "cred-1",
            "heartbeat_interval_seconds": 30,
        },
    }
    if extra:
        cfg["lenlion_platform"].update(extra)
    hermes_home.mkdir(parents=True, exist_ok=True)
    (hermes_home / "config.yaml").write_text(yaml.safe_dump(cfg), encoding="utf-8")


class TestLeaseCache:
    def test_returns_token_on_valid_lease(self):
        from plugins.lenlion_edge.lease_cache import LeaseCache

        client = MagicMock()
        client.heartbeat.return_value = _heartbeat("tok-1")
        cache = LeaseCache(client)
        assert cache.get_agent_token() == "tok-1"
        assert cache.policy is not None
        assert cache.policy.etag == "etag-1"
        client.heartbeat.assert_called_once()

    def test_refreshes_when_near_expiry(self):
        from plugins.lenlion_edge.lease_cache import LeaseCache

        client = MagicMock()
        client.heartbeat.side_effect = [
            _heartbeat("tok-old", expires_in=10),  # below refresh threshold
            _heartbeat("tok-new", expires_in=600),
        ]
        cache = LeaseCache(client)
        assert cache.get_agent_token() == "tok-old"
        assert cache.get_agent_token() == "tok-new"
        assert client.heartbeat.call_count == 2

    def test_fail_closed_when_heartbeat_fails(self):
        from plugins.lenlion_edge.lease_cache import LeaseCache
        from plugins.lenlion_edge.protocol import LeaseUnavailableError

        client = MagicMock()
        client.heartbeat.side_effect = RuntimeError("network down")
        cache = LeaseCache(client)
        with pytest.raises(LeaseUnavailableError, match="failed to refresh"):
            cache.get_agent_token()


class TestPreToolCall:
    def test_blocks_high_risk_without_lease(self, tmp_path, monkeypatch):
        from plugins import lenlion_edge

        hermes_home = tmp_path / "hermes"
        _write_managed_config(hermes_home)
        monkeypatch.setenv("HERMES_HOME", str(hermes_home))

        client = MagicMock()
        client.heartbeat.side_effect = RuntimeError("boom")
        lenlion_edge._client = client
        lenlion_edge._cache = __import__(
            "plugins.lenlion_edge.lease_cache", fromlist=["LeaseCache"]
        ).LeaseCache(client)
        lenlion_edge._managed_enabled = True

        result = lenlion_edge._on_pre_tool_call(
            tool_name="terminal",
            args={"command": "ls"},
        )
        assert result is not None
        assert result["action"] == "block"
        assert "lease" in result["message"].lower() or "failed" in result["message"].lower()

    def test_allows_low_risk_without_lease_check(self):
        from plugins import lenlion_edge

        lenlion_edge._managed_enabled = True
        lenlion_edge._cache = MagicMock()
        result = lenlion_edge._on_pre_tool_call(tool_name="web_search", args={})
        assert result is None
        lenlion_edge._cache.get_agent_token.assert_not_called()

    def test_blocks_hardline_even_with_lease(self):
        from plugins import lenlion_edge
        from plugins.lenlion_edge.lease_cache import LeaseCache

        client = MagicMock()
        client.heartbeat.return_value = _heartbeat()
        lenlion_edge._client = client
        lenlion_edge._cache = LeaseCache(client)
        lenlion_edge._managed_enabled = True

        result = lenlion_edge._on_pre_tool_call(
            tool_name="terminal",
            args={"command": "rm -rf /"},
        )
        assert result is not None
        assert result["action"] == "block"
        assert "hardline" in result["message"].lower()


class TestPluginRegistration:
    def test_register_injects_token_provider(self, tmp_path, monkeypatch):
        from hermes_cli.runtime_provider import get_runtime_token_provider
        from plugins import lenlion_edge

        hermes_home = tmp_path / "hermes"
        _write_managed_config(hermes_home)
        monkeypatch.setenv("HERMES_HOME", str(hermes_home))

        fake_client = MagicMock()
        fake_client.heartbeat.return_value = _heartbeat("tok-reg")

        class _FakeCP:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

            def close(self):
                pass

            def heartbeat(self, **kwargs):
                return fake_client.heartbeat(**kwargs)

        monkeypatch.setattr(lenlion_edge, "ControlPlaneClient", _FakeCP)

        ctx = MagicMock()
        lenlion_edge.register(ctx)
        getter = get_runtime_token_provider("lenlion-cloud")
        assert getter is not None
        assert getter() == "tok-reg"
        ctx.register_hook.assert_any_call("pre_tool_call", lenlion_edge._on_pre_tool_call)
        ctx.register_hook.assert_any_call(
            "on_session_start", lenlion_edge._on_session_start
        )

    def test_bundled_plugin_loads_when_enabled(self, tmp_path, monkeypatch):
        hermes_home = tmp_path / "hermes"
        _write_managed_config(hermes_home)
        monkeypatch.setenv("HERMES_HOME", str(hermes_home))

        from plugins import lenlion_edge as edge_mod

        class _FakeCP:
            def __init__(self, **kwargs):
                pass

            def close(self):
                pass

            def heartbeat(self, **kwargs):
                return _heartbeat("tok-load")

        monkeypatch.setattr(edge_mod, "ControlPlaneClient", _FakeCP)

        mgr = PluginManager()
        mgr.discover_and_load()
        assert "lenlion_edge" in mgr._plugins
        assert mgr._plugins["lenlion_edge"].enabled
        from hermes_cli.runtime_provider import get_runtime_token_provider

        assert get_runtime_token_provider("lenlion-cloud") is not None


class TestEnrollConfigMerge:
    def test_write_managed_config_appends_plugin(self, tmp_path, monkeypatch):
        import importlib.util

        # tests/plugins -> lenlion_agent -> repo root
        repo_root = Path(__file__).resolve().parents[3]
        script = repo_root / "lenlion_platform" / "scripts" / "enroll_agent.py"
        spec = importlib.util.spec_from_file_location("enroll_agent", script)
        assert spec and spec.loader
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        hermes_home = tmp_path / ".hermes"
        hermes_home.mkdir()
        (hermes_home / "config.yaml").write_text(
            yaml.safe_dump({"plugins": {"enabled": ["security-guidance"]}}),
            encoding="utf-8",
        )
        monkeypatch.setenv("HERMES_HOME", str(hermes_home))

        path = mod.write_managed_config(
            control_plane_url="http://127.0.0.1:8080",
            model_gateway_url="http://127.0.0.1:8081",
            agent_id="a1",
            tenant_id="t1",
            node_credential="c1",
        )
        cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert cfg["plugins"]["enabled"] == ["security-guidance", "lenlion_edge"]
        assert cfg["lenlion_platform"]["control_plane_url"] == "http://127.0.0.1:8080"
        assert cfg["lenlion_platform"]["model_gateway_url"] == "http://127.0.0.1:8081"
        assert cfg["model"]["provider"] == "lenlion-cloud"
