from __future__ import annotations

from control_plane import store


def record_chat_usage(
    *,
    tenant_id: str,
    agent_id: str,
    model: str,
    usage: dict | None,
    session_id: str | None = None,
) -> None:
    usage = usage or {}
    store.record_model_usage(
        tenant_id=tenant_id,
        agent_id=agent_id,
        session_id=session_id,
        provider="openai-compat",
        model=model,
        input_tokens=int(usage.get("prompt_tokens") or 0),
        output_tokens=int(usage.get("completion_tokens") or 0),
    )
