from __future__ import annotations

import hashlib
import os
import secrets
import uuid

from fastapi import HTTPException, status


def get_admin_token() -> str:
    token = os.environ.get("ADMIN_TOKEN", "").strip()
    if not token:
        raise RuntimeError("ADMIN_TOKEN is required")
    return token


def verify_admin_header(authorization: str | None) -> None:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing admin token",
        )
    token = authorization.removeprefix("Bearer ").strip()
    if token != get_admin_token():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="invalid admin token",
        )


def hash_secret(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def verify_secret(value: str, value_hash: str) -> bool:
    return secrets.compare_digest(hash_secret(value), value_hash)


def new_id(prefix: str = "") -> str:
    return f"{prefix}{uuid.uuid4().hex}"


def new_token() -> str:
    return secrets.token_urlsafe(32)
