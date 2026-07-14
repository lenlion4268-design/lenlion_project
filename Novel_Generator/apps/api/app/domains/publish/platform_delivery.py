import httpx

from app.core.config import settings
from app.domains.publish.models import Publication
from app.domains.publish.platform_payload import build_platform_payload


class PlatformDelivery:
    def deliver(
        self,
        publication: Publication,
        *,
        markdown_content: str,
        download_url: str,
    ) -> tuple[str | None, str | None]:
        if not settings.publish_platform_api_url:
            return None, "PUBLISH_PLATFORM_API_URL is not configured"
        if not settings.publish_platform_api_token:
            return None, "PUBLISH_PLATFORM_API_TOKEN is not configured"

        payload = build_platform_payload(
            publication,
            markdown_content=markdown_content,
            download_url=download_url,
            preset=settings.publish_platform_preset,
        )
        headers = {
            "Authorization": f"Bearer {settings.publish_platform_api_token}",
            "Content-Type": "application/json",
        }
        try:
            response = httpx.post(
                settings.publish_platform_api_url,
                headers=headers,
                json=payload,
                timeout=30.0,
            )
            response.raise_for_status()
            body = response.json() if response.content else {}
            external_ref = None
            if isinstance(body, dict):
                external_ref = body.get("id") or body.get("publication_id")
            return external_ref, None
        except httpx.HTTPError as exc:
            return None, str(exc)
