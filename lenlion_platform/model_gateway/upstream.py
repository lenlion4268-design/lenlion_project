from __future__ import annotations

import os

import httpx


def get_upstream_base_url() -> str:
    return os.environ.get("OPENAI_COMPAT_BASE_URL", "").strip().rstrip("/")


def get_upstream_api_key() -> str:
    key = os.environ.get("UPSTREAM_OPENAI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("UPSTREAM_OPENAI_API_KEY is required")
    return key


async def forward_chat_completions(
    payload: dict,
    *,
    client: httpx.AsyncClient | None = None,
) -> httpx.Response:
    base_url = get_upstream_base_url()
    if not base_url:
        raise RuntimeError("OPENAI_COMPAT_BASE_URL is required")
    owns_client = client is None
    http = client or httpx.AsyncClient()
    try:
        return await http.post(
            f"{base_url}/chat/completions",
            json=payload,
            headers={
                "Authorization": f"Bearer {get_upstream_api_key()}",
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )
    finally:
        if owns_client:
            await http.aclose()


async def forward_models(*, client: httpx.AsyncClient | None = None) -> httpx.Response:
    base_url = get_upstream_base_url()
    if not base_url:
        raise RuntimeError("OPENAI_COMPAT_BASE_URL is required")
    owns_client = client is None
    http = client or httpx.AsyncClient()
    try:
        return await http.get(
            f"{base_url}/models",
            headers={"Authorization": f"Bearer {get_upstream_api_key()}"},
            timeout=30.0,
        )
    finally:
        if owns_client:
            await http.aclose()
