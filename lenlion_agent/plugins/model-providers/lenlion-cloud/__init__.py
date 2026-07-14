"""Lenlion Cloud managed model-gateway provider profile."""

from providers import register_provider
from providers.base import ProviderProfile

lenlion_cloud = ProviderProfile(
    name="lenlion-cloud",
    aliases=("lenlion", "lenlion-platform"),
    display_name="Lenlion Cloud",
    description="Lenlion managed model gateway",
    base_url="",
    auth_type="api_key",
    supports_health_check=False,
)

register_provider(lenlion_cloud)
