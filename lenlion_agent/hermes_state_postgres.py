"""PostgreSQL backend for Hermes session storage (Docker / DATABASE_URL).

When ``DATABASE_URL`` is set, ``SessionDB()`` uses this backend instead of the
local ``state.db`` SQLite file. With the same env var, ``load_config`` /
``save_config`` and ``load_env`` / ``save_env_value`` store platform config
and secrets in Postgres (``platform_config``, ``platform_secrets``).
"""

from __future__ import annotations

import logging
import os
import random
import re
import threading
import time
from pathlib import Path
from typing import Any, Callable, List, Optional, Sequence, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

_PLACEHOLDER_RE = re.compile(r"\?")
_JSON_EXTRACT_RE = re.compile(
    r"json_extract\(COALESCE\(([^,]+),\s*'\{\}'\),\s*'\$\.([^']+)'\)",
    re.IGNORECASE,
)
_JSON_SET_RE = re.compile(
    r"json_set\(COALESCE\(([^,]+),\s*'\{\}'\),\s*'\$\.([^']+)',\s*([^)]+)\)",
    re.IGNORECASE,
)


def resolve_database_url() -> str:
    url = (os.environ.get("DATABASE_URL") or "").strip()
    if url:
        return url
    try:
        from hermes_cli.config import get_env_value

        url = (get_env_value("DATABASE_URL") or "").strip()
    except Exception:
        url = ""
    return url


def should_use_postgres(db_path=None, read_only: bool = False) -> bool:
    if read_only:
        return False
    if not resolve_database_url():
        return False
    if db_path is not None:
        from hermes_state import DEFAULT_DB_PATH

        if db_path != DEFAULT_DB_PATH:
            return False
    return True


class _PgRow(dict):
    """sqlite3.Row-like mapping."""


class _PgCursor:
    def __init__(self, cur):
        self._cur = cur
        self.rowcount = getattr(cur, "rowcount", 0) or 0

    def fetchone(self):
        row = self._cur.fetchone()
        if row is None:
            return None
        if isinstance(row, dict):
            return _PgRow(row)
        cols = [d[0] for d in self._cur.description]
        return _PgRow(dict(zip(cols, row)))

    def fetchall(self) -> List[_PgRow]:
        rows = self._cur.fetchall()
        if not rows:
            return []
        if isinstance(rows[0], dict):
            return [_PgRow(r) for r in rows]
        cols = [d[0] for d in self._cur.description]
        return [_PgRow(dict(zip(cols, r))) for r in rows]


def _translate_sql(sql: str) -> str:
    stripped = sql.strip()
    upper = stripped.upper()
    if upper.startswith("PRAGMA"):
        return "SELECT 1 WHERE FALSE"
    if "SQLITE_MASTER" in upper:
        return "SELECT 0 WHERE FALSE"

    sql = re.sub(r"\bINSERT OR IGNORE INTO\b", "INSERT INTO", sql, flags=re.IGNORECASE)
    sql = re.sub(r"\bINSERT OR REPLACE INTO\b", "INSERT INTO", sql, flags=re.IGNORECASE)

    if re.search(r"\bINSERT INTO\b", sql, re.IGNORECASE) and "ON CONFLICT" not in upper:
        if re.search(r"\bINTO\s+sessions\b", sql, re.IGNORECASE):
            sql = sql.rstrip().rstrip(";") + " ON CONFLICT (id) DO NOTHING"
        elif re.search(r"\bINTO\s+state_meta\b", sql, re.IGNORECASE):
            sql = sql.rstrip().rstrip(";") + " ON CONFLICT (key) DO NOTHING"
        elif re.search(r"\bINTO\s+compression_locks\b", sql, re.IGNORECASE):
            sql = sql.rstrip().rstrip(";") + " ON CONFLICT (session_id) DO NOTHING"

    sql = _JSON_EXTRACT_RE.sub(r"(\1::jsonb->>'\2')", sql)
    sql = _JSON_SET_RE.sub(
        r"jsonb_set(COALESCE(\1::jsonb, '{}'::jsonb), '{\2}', to_jsonb(\3::text), true)::text",
        sql,
    )
    sql = re.sub(r"\binstr\(", "position(", sql, flags=re.IGNORECASE)
    sql = re.sub(r"\bsubstr\(", "substring(", sql, flags=re.IGNORECASE)
    sql = sql.replace("LIKE ? ESCAPE '\\\\'", "ILIKE %s ESCAPE E'\\\\'")
    if "%s" not in sql:
        sql = _PLACEHOLDER_RE.sub("%s", sql)
    return sql


class PgCompatConnection:
    def __init__(self, conn):
        self._conn = conn

    def cursor(self):
        return self

    def execute(self, sql: str, params: Sequence[Any] = ()):
        sql = _translate_sql(sql)
        cur = self._conn.cursor()
        cur.execute(sql, tuple(params) if params else None)
        wrapper = _PgCursor(cur)
        return wrapper

    def executescript(self, sql: str):
        for stmt in sql.split(";"):
            piece = stmt.strip()
            if piece:
                self.execute(piece)

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()


def _init_pg_schema(conn: PgCompatConnection, schema_version: int) -> None:
    init_path = Path(__file__).resolve().parent / "docker" / "postgres" / "init.sql"
    if init_path.is_file():
        conn.executescript(init_path.read_text(encoding="utf-8"))
    conn.execute(
        "INSERT INTO schema_version (version) SELECT %s "
        "WHERE NOT EXISTS (SELECT 1 FROM schema_version)",
        (schema_version,),
    )
    conn.commit()


def build_postgres_session_db():
    """Construct a Postgres-backed session store."""
    import psycopg

    from hermes_state import SCHEMA_VERSION, SessionDB, _set_last_init_error

    url = resolve_database_url()
    if not url:
        raise RuntimeError("DATABASE_URL is not configured")

    inst = PostgresSessionDB.__new__(PostgresSessionDB)
    inst.db_path = None
    inst.read_only = False
    inst._postgres = True
    inst._lock = threading.Lock()
    inst._write_count = 0
    inst._fts_enabled = False
    inst._fts_unavailable_warned = False
    inst._conn = None
    try:
        raw = psycopg.connect(url, autocommit=False)
        inst._conn = PgCompatConnection(raw)
        _init_pg_schema(inst._conn, SCHEMA_VERSION)
    except Exception as exc:
        _set_last_init_error(f"{type(exc).__name__}: {exc}")
        raise
    return inst


class PostgresSessionDB:
    """Drop-in SessionDB replacement backed by PostgreSQL."""

    _WRITE_MAX_RETRIES = 10
    _WRITE_RETRY_MIN_S = 0.020
    _WRITE_RETRY_MAX_S = 0.150

    def __init__(self):
        raise RuntimeError("Use build_postgres_session_db() or SessionDB() factory")

    def _execute_write(self, fn: Callable[[PgCompatConnection], T]) -> T:
        import psycopg

        last_err: Exception | None = None
        for attempt in range(self._WRITE_MAX_RETRIES):
            try:
                with self._lock:
                    self._conn.execute("BEGIN")
                    try:
                        result = fn(self._conn)
                        self._conn.commit()
                    except BaseException:
                        try:
                            self._conn.rollback()
                        except Exception:
                            pass
                        raise
                self._write_count += 1
                return result
            except psycopg.Error as exc:
                err_msg = str(exc).lower()
                if "deadlock" in err_msg or "could not serialize" in err_msg:
                    last_err = exc
                    if attempt < self._WRITE_MAX_RETRIES - 1:
                        time.sleep(random.uniform(self._WRITE_RETRY_MIN_S, self._WRITE_RETRY_MAX_S))
                        continue
                raise
        raise last_err or RuntimeError("postgres write failed after retries")

    def _try_wal_checkpoint(self) -> None:
        return

    def close(self) -> None:
        with self._lock:
            if self._conn:
                self._conn.close()
                self._conn = None

    def search_messages(self, query: str, source_filter=None, exclude_sources=None,
                        role_filter=None, limit: int = 20, offset: int = 0,
                        sort: str = None, include_inactive: bool = False):
        from hermes_state import SessionDB

        if not query or not query.strip():
            return []
        raw_query = query.strip().strip('"')
        non_op_tokens = [
            t for t in raw_query.split()
            if t.upper() not in {"AND", "OR", "NOT"}
        ] or [raw_query]
        token_clauses = []
        like_params: list = []
        for tok in non_op_tokens:
            esc = tok.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            token_clauses.append(
                "(m.content ILIKE %s ESCAPE E'\\\\' OR m.tool_name ILIKE %s ESCAPE E'\\\\' "
                "OR m.tool_calls ILIKE %s ESCAPE E'\\\\')"
            )
            like_params += [f"%{esc}%", f"%{esc}%", f"%{esc}%"]
        like_where = [f"({' OR '.join(token_clauses)})"]
        if not include_inactive:
            like_where.append("m.active = 1")
        if source_filter is not None:
            like_where.append(f"s.source IN ({','.join('%s' for _ in source_filter)})")
            like_params.extend(source_filter)
        if exclude_sources is not None:
            like_where.append(f"s.source NOT IN ({','.join('%s' for _ in exclude_sources)})")
            like_params.extend(exclude_sources)
        if role_filter:
            like_where.append(f"m.role IN ({','.join('%s' for _ in role_filter)})")
            like_params.extend(role_filter)
        order = "ORDER BY m.timestamp DESC"
        if sort and str(sort).strip().lower() == "oldest":
            order = "ORDER BY m.timestamp ASC"
        like_sql = f"""
            SELECT m.id, m.session_id, m.role,
                   substring(m.content from greatest(1, position(%s in m.content) - 40) for 120) AS snippet,
                   m.content, m.timestamp, m.tool_name,
                   s.source, s.model, s.started_at AS session_started
            FROM messages m
            JOIN sessions s ON s.id = m.session_id
            WHERE {' AND '.join(like_where)}
            {order}
            LIMIT %s OFFSET %s
        """
        params = [non_op_tokens[0], *like_params, limit, offset]
        with self._lock:
            cur = self._conn.execute(like_sql, params)
            matches = [dict(row) for row in cur.fetchall()]
        for match in matches:
            match.pop("content", None)
            match["context"] = []
        return matches

    def __getattr__(self, name: str):
        from hermes_state import SessionDB

        attr = getattr(SessionDB, name)
        if callable(attr):
            def _delegate(*args, **kwargs):
                return attr(self, *args, **kwargs)
            return _delegate
        return attr
