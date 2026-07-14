"""Runtime resolution tests for lenlion-cloud provider."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml


@pytest.fixture(autouse=True)
def _clear_token_providers():
    from hermes_cli.runtime_provider import clear_runtime_token_providers

    clear_runtime_token_providers()
    yield
    clear_runtime_token_providers()


def _write_config(hermes_home: Path, **platform_extra) -> None:
    platform = {
        "enabled": True,
        "control_plane_url": "http://127.0.0.1:8080",
        "model_gateway_url": "http://127.0.0.1:8081",
        "agent_id": "agent-1",
        "node_credential": "cred-1",
    }
    platform.update(platform_extra)
    cfg = {
        "model": {"provider": "lenlion-cloud", "default": "gpt-4o-mini"},
        "lenlion_platform": platform,
    }
    hermes_home.mkdir(parents=True, exist_ok=True)
    (hermes_home / "config.yaml").write_text(yaml.safe_dump(cfg), encoding="utf-8")


class TestLenlionCloudRuntime:
    def test_returns_callable_api_key_and_gateway_v1(self, tmp_path, monkeypatch):
        from hermes_cli.runtime_provider import (
            register_runtime_token_provider,
            resolve_runtime_provider,
        )

        hermes_home = tmp_path / "hermes"
        _write_config(hermes_home)
        monkeypatch.setenv("HERMES_HOME", str(hermes_home))

        register_runtime_token_provider("lenlion-cloud", lambda: "lease-token")
        runtime = resolve_runtime_provider(requested="lenlion-cloud")
        assert runtime["provider"] == "lenlion-cloud"
        assert runtime["api_mode"] == "chat_completions"
        assert runtime["base_url"] == "http://127.0.0.1:8081/v1"
        assert callable(runtime["api_key"])
        assert not isinstance(runtime["api_key"], str)
        assert runtime["api_key"]() == "lease-token"

    def test_alias_short_circuits(self, tmp_path, monkeypatch):
        from hermes_cli.runtime_provider import (
            register_runtime_token_provider,
            resolve_runtime_provider,
        )

        hermes_home = tmp_path / "hermes"
        _write_config(hermes_home)
        monkeypatch.setenv("HERMES_HOME", str(hermes_home))
        register_runtime_token_provider("lenlion-cloud", lambda: "tok")

        for alias in ("lenlion", "lenlion-platform"):
            runtime = resolve_runtime_provider(requested=alias)
            assert runtime["provider"] == "lenlion-cloud"
            assert runtime["base_url"].endswith("/v1")

    def test_callable_fail_closed_when_unregistered(self, tmp_path, monkeypatch):
        from hermes_cli.auth import AuthError
        from hermes_cli.runtime_provider import resolve_runtime_provider

        hermes_home = tmp_path / "hermes"
        _write_config(hermes_home)
        monkeypatch.setenv("HERMES_HOME", str(hermes_home))

        runtime = resolve_runtime_provider(requested="lenlion-cloud")
        assert callable(runtime["api_key"])
        with pytest.raises(AuthError, match="not registered"):
            runtime["api_key"]()

    def test_missing_model_gateway_url_raises(self, tmp_path, monkeypatch):
        from hermes_cli.auth import AuthError
        from hermes_cli.runtime_provider import resolve_runtime_provider

        hermes_home = tmp_path / "hermes"
        _write_config(hermes_home, model_gateway_url="")
        # wipe gateway url explicitly
        cfg_path = hermes_home / "config.yaml"
        cfg = yaml.safe_load(cfg_path.read_text())
        cfg["lenlion_platform"].pop("model_gateway_url", None)
        cfg_path.write_text(yaml.safe_dump(cfg))
        monkeypatch.setenv("HERMES_HOME", str(hermes_home))

        with pytest.raises(AuthError, match="model_gateway_url"):
            resolve_runtime_provider(requested="lenlion-cloud")

    def test_does_not_fall_through_to_openrouter(self, tmp_path, monkeypatch):
        from hermes_cli.runtime_provider import (
            register_runtime_token_provider,
            resolve_runtime_provider,
        )

        hermes_home = tmp_path / "hermes"
        _write_config(hermes_home)
        monkeypatch.setenv("HERMES_HOME", str(hermes_home))
        monkeypatch.setenv("OPENROUTER_API_KEY", "or-should-not-win")
        register_runtime_token_provider("lenlion-cloud", lambda: "tok")

        runtime = resolve_runtime_provider(requested="lenlion-cloud")
        assert runtime["provider"] == "lenlion-cloud"
        assert "openrouter" not in runtime["base_url"]
        assert runtime["source"] == "lenlion-cloud"
