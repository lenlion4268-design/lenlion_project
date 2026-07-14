"""Real Postgres smoke: dual init scripts + shared db connection layer.

Skipped unless LENLION_PLATFORM_POSTGRES_SMOKE=1 and DATABASE_URL point at a
live pgvector Postgres. Memory-store unit tests do not cover this path.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from psycopg import Connection

from control_plane import db

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENT_INIT = REPO_ROOT / "lenlion_agent" / "docker" / "postgres" / "init.sql"
PLATFORM_INIT = Path(__file__).resolve().parents[1] / "db" / "init.sql"

REQUIRED_TABLES = (
    "schema_version",
    "sessions",
    "messages",
    "platform_schema_version",
    "tenants",
    "agents",
    "leases",
)


def _apply_sql(conn: Connection, path: Path) -> None:
    # Strip -- line comments before splitting; init.sql comments may contain ';'.
    raw = path.read_text(encoding="utf-8")
    cleaned = "\n".join(line.split("--", 1)[0] for line in raw.splitlines())
    for stmt in cleaned.split(";"):
        piece = stmt.strip()
        if piece:
            conn.execute(piece)


@pytest.mark.postgres_smoke
def test_dual_init_scripts_and_shared_db_layer() -> None:
    if os.environ.get("LENLION_PLATFORM_POSTGRES_SMOKE") != "1":
        pytest.skip("set LENLION_PLATFORM_POSTGRES_SMOKE=1 with a live DATABASE_URL")

    assert AGENT_INIT.is_file(), f"missing agent init: {AGENT_INIT}"
    assert PLATFORM_INIT.is_file(), f"missing platform init: {PLATFORM_INIT}"

    url = db.get_database_url()
    assert url.startswith("postgresql"), url

    with db.connect(autocommit=True) as conn:
        _apply_sql(conn, AGENT_INIT)
        _apply_sql(conn, PLATFORM_INIT)

    with db.transaction() as conn:
        platform_version = conn.execute(
            "SELECT version FROM platform_schema_version"
        ).fetchone()
        assert platform_version is not None
        assert platform_version[0] == 1

        agent_version = conn.execute("SELECT version FROM schema_version").fetchone()
        assert agent_version is not None
        assert agent_version[0] >= 1

        for table in REQUIRED_TABLES:
            row = conn.execute(
                """
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = %s
                """,
                (table,),
            ).fetchone()
            assert row is not None, f"expected table {table!r} after dual init"
