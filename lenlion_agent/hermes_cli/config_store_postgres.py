"""PostgreSQL-backed config and secrets store for Docker deployments.

When ``DATABASE_URL`` is set, ``load_config`` / ``save_config`` and
``load_env`` / ``save_env_value`` read and write through these tables
instead of relying on ``config.yaml`` / ``.env`` as the source of truth.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

_LOCK = threading.Lock()
_CONN = None
_TABLES_READY = False

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS platform_config (
    profile_id TEXT PRIMARY KEY,
    config JSONB NOT NULL,
    updated_at DOUBLE PRECISION NOT NULL
);

CREATE TABLE IF NOT EXISTS platform_secrets (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at DOUBLE PRECISION NOT NULL
);
"""


def postgres_store_enabled() -> bool:
    try:
        from hermes_state_postgres import resolve_database_url

        return bool(resolve_database_url())
    except Exception:
        return bool((__import__("os").environ.get("DATABASE_URL") or "").strip())


def _profile_id() -> str:
    from hermes_cli.config import get_hermes_home

    return str(get_hermes_home())


def _connect():
    global _CONN
    import psycopg
    from hermes_state_postgres import resolve_database_url

    url = resolve_database_url()
    if not url:
        raise RuntimeError("DATABASE_URL is not configured")
    if _CONN is None or getattr(_CONN, "closed", False):
        _CONN = psycopg.connect(url, autocommit=False)
    return _CONN


def _ensure_tables(conn) -> None:
    global _TABLES_READY
    if _TABLES_READY:
        return
    with conn.cursor() as cur:
        cur.execute(_SCHEMA_SQL)
    conn.commit()
    _TABLES_READY = True


def _config_cache_key(updated_at: float) -> Tuple[int, int]:
    return (int(updated_at * 1_000_000), 0)


def load_raw_config_from_db() -> Tuple[Optional[Dict[str, Any]], Optional[float]]:
    """Return (raw config dict, updated_at) or (None, None) if missing."""
    if not postgres_store_enabled():
        return None, None
    with _LOCK:
        conn = _connect()
        _ensure_tables(conn)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT config, updated_at FROM platform_config WHERE profile_id = %s",
                (_profile_id(),),
            )
            row = cur.fetchone()
        if not row:
            return None, None
        config, updated_at = row[0], float(row[1])
        if isinstance(config, str):
            config = json.loads(config)
        if not isinstance(config, dict):
            return None, None
        return config, updated_at


def save_raw_config_to_db(config: Dict[str, Any]) -> float:
    updated_at = time.time()
    payload = json.loads(json.dumps(config))
    with _LOCK:
        conn = _connect()
        _ensure_tables(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO platform_config (profile_id, config, updated_at)
                VALUES (%s, %s::jsonb, %s)
                ON CONFLICT (profile_id) DO UPDATE SET
                    config = EXCLUDED.config,
                    updated_at = EXCLUDED.updated_at
                """,
                (_profile_id(), json.dumps(payload), updated_at),
            )
        conn.commit()
    return updated_at


def load_secrets_from_db() -> Dict[str, str]:
    if not postgres_store_enabled():
        return {}
    with _LOCK:
        conn = _connect()
        _ensure_tables(conn)
        with conn.cursor() as cur:
            cur.execute("SELECT key, value FROM platform_secrets ORDER BY key")
            rows = cur.fetchall()
    return {str(k): str(v) for k, v in rows}


def save_secret_to_db(key: str, value: str) -> None:
    updated_at = time.time()
    with _LOCK:
        conn = _connect()
        _ensure_tables(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO platform_secrets (key, value, updated_at)
                VALUES (%s, %s, %s)
                ON CONFLICT (key) DO UPDATE SET
                    value = EXCLUDED.value,
                    updated_at = EXCLUDED.updated_at
                """,
                (key, value, updated_at),
            )
        conn.commit()


def delete_secret_from_db(key: str) -> bool:
    with _LOCK:
        conn = _connect()
        _ensure_tables(conn)
        with conn.cursor() as cur:
            cur.execute("DELETE FROM platform_secrets WHERE key = %s", (key,))
            deleted = cur.rowcount > 0
        conn.commit()
    return deleted


def env_db_cache_key() -> Tuple[str, float, int]:
    """Return (profile_id, max_updated_at, row_count) for load_env cache."""
    if not postgres_store_enabled():
        return _profile_id(), 0.0, 0
    with _LOCK:
        conn = _connect()
        _ensure_tables(conn)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COALESCE(MAX(updated_at), 0), COUNT(*) FROM platform_secrets"
            )
            updated_at, count = cur.fetchone()
    return _profile_id(), float(updated_at), int(count)


def migrate_file_config_to_db_if_empty(raw: Dict[str, Any]) -> None:
    if not raw:
        return
    existing, _ = load_raw_config_from_db()
    if existing is None:
        save_raw_config_to_db(raw)
        logger.info("Migrated config.yaml into Postgres for profile %s", _profile_id())


def migrate_file_secrets_to_db_if_empty(secrets: Dict[str, str]) -> None:
    if not secrets:
        return
    if load_secrets_from_db():
        return
    for key, value in secrets.items():
        save_secret_to_db(key, value)
    logger.info("Migrated .env (%d keys) into Postgres", len(secrets))
