from __future__ import annotations

import os
from typing import Annotated, Any

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse

from control_plane.app import gateway_auth_error
from control_plane.leases import (
    ExpiredTokenError,
    InvalidTokenError,
    RevokedTokenError,
    verify_agent_token,
)
from control_plane.policies import resolve_policy
from control_plane import store
from model_gateway import upstream
from model_gateway.usage import record_chat_usage


def _extract_bearer(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing agent token",
        )
    return authorization.removeprefix("Bearer ").strip()


def _authorize_model_request(
    authorization: Annotated[str | None, Header()] = None,
) -> tuple[Any, Any]:
    token = _extract_bearer(authorization)
    try:
        claims = verify_agent_token(token)
    except (RevokedTokenError, ExpiredTokenError, InvalidTokenError) as exc:
        raise gateway_auth_error(exc) from exc
    if store.is_agent_revoked(claims.agent_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="agent revoked",
        )
    policy = resolve_policy(claims.tenant_id, claims.agent_id, claims.policy_etag)
    if policy is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="policy missing or stale",
        )
    return claims, policy


def create_app(*, http_client: httpx.AsyncClient | None = None) -> FastAPI:
    app = FastAPI(title="lenlion-model-gateway")
    app.state.http_client = http_client

    @app.get("/healthz")
    def healthz() -> dict[str, str | bool]:
        return {"ok": True, "service": "model-gateway"}

    @app.get("/v1/models")
    async def list_models(
        auth: Annotated[tuple[Any, Any], Depends(_authorize_model_request)],
    ) -> JSONResponse:
        claims, policy = auth
        if not policy.allowed_models:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="no models allowed",
            )
        client = app.state.http_client
        if client is not None:
            response = await upstream.forward_models(client=client)
            return JSONResponse(status_code=response.status_code, content=response.json())
        data = {
            "object": "list",
            "data": [{"id": model, "object": "model"} for model in policy.allowed_models],
        }
        return JSONResponse(content=data)

    @app.post("/v1/chat/completions")
    async def chat_completions(
        request: Request,
        auth: Annotated[tuple[Any, Any], Depends(_authorize_model_request)],
    ) -> JSONResponse:
        claims, policy = auth
        body = await request.json()
        model = body.get("model")
        if not isinstance(model, str) or not model:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="model is required",
            )
        if not policy.allowed_models or model not in policy.allowed_models:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="model not allowed",
            )
        client = app.state.http_client
        if client is None:
            if not os.environ.get("OPENAI_COMPAT_BASE_URL", "").strip():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="upstream not configured",
                )
            client = httpx.AsyncClient()
            owns_client = True
        else:
            owns_client = False
        try:
            response = await upstream.forward_chat_completions(body, client=client)
        finally:
            if owns_client:
                await client.aclose()
        if response.status_code >= 400:
            return JSONResponse(
                status_code=response.status_code,
                content=response.json(),
            )
        payload = response.json()
        record_chat_usage(
            tenant_id=claims.tenant_id,
            agent_id=claims.agent_id,
            model=model,
            usage=payload.get("usage"),
        )
        return JSONResponse(content=payload)

    return app
