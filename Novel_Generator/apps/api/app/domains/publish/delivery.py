import httpx

from app.core.config import settings
from app.domains.publish.models import Publication


class WebhookDelivery:
    def deliver(self, publication: Publication, *, content: str, download_url: str) -> tuple[str | None, str | None]:
        if not settings.publish_webhook_url:
            return None, "PUBLISH_WEBHOOK_URL is not configured"

        headers = {"Content-Type": "application/json"}
        if settings.publish_webhook_secret:
            headers["X-Novel-Webhook-Secret"] = settings.publish_webhook_secret

        payload = {
            "publication_id": publication.id,
            "project_id": publication.project_id,
            "volume_id": publication.volume_id,
            "title": publication.title,
            "format": publication.format,
            "chapter_count": publication.chapter_count,
            "word_count": publication.word_count,
            "download_url": download_url,
            "content_preview": content[:500],
        }
        try:
            response = httpx.post(
                settings.publish_webhook_url,
                headers=headers,
                json=payload,
                timeout=30.0,
            )
            response.raise_for_status()
            external_ref = response.headers.get("X-Publication-Ref") or response.headers.get("Location")
            return external_ref, None
        except httpx.HTTPError as exc:
            return None, str(exc)
