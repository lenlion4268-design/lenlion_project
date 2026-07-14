"""Discovery tests for the lenlion-cloud provider profile."""

from __future__ import annotations


def test_lenlion_cloud_profile_is_discoverable():
    import model_tools  # noqa: F401 — triggers provider discovery
    import providers

    profile = providers.get_provider_profile("lenlion-cloud")
    assert profile is not None
    assert profile.name == "lenlion-cloud"
    assert profile.supports_health_check is False
    assert "lenlion" in profile.aliases
    assert "lenlion-platform" in profile.aliases


def test_lenlion_cloud_alias_resolves():
    import model_tools  # noqa: F401
    import providers

    assert providers.get_provider_profile("lenlion").name == "lenlion-cloud"
    assert providers.get_provider_profile("lenlion-platform").name == "lenlion-cloud"
