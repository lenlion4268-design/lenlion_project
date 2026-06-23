# Lenlion Platform

Cloud control plane and model gateway for the Lenlion agent runtime.

**Current status:** Phase 1 complete — package skeleton, shared DB layer, schema
boundary, health checks, and Docker Compose bootstrap. Auth, leases, enrollment,
and gateway enforcement land in Phase 2+.

**Deployment:** Platform services run in Docker (this compose file). **Lenlion Agent
runs on the developer/user machine** and connects to the cloud Postgres via
`DATABASE_URL`. Apply agent schema separately:

```bash
psql "$DATABASE_URL" -f ../lenlion_agent/docker/postgres/init.sql
psql "$DATABASE_URL" -f db/init.sql
```

## Database boundary

**Decision: same Postgres instance, same database, co-located tables.**

Platform control tables (`tenants`, `agents`, `leases`, …) live in the same
Postgres database as the existing `lenlion_agent` session and config tables
(`sessions`, `messages`, `platform_config`, `platform_secrets`).

| Owner | Migration marker | Tables |
|-------|------------------|--------|
| `lenlion_agent` | `schema_version` | sessions, messages, state_meta, compression_locks, platform_config, platform_secrets |
| `lenlion_platform` | `platform_schema_version` | tenants, agents, leases, policies, approvals, audit_events, skills, kb_documents, model_usage |

`lenlion_platform/db/init.sql` does **not** recreate agent-owned tables. In
combined deployments, apply both init scripts to the same database (agent init
first, then platform init).

## Local development

```bash
cd lenlion_platform
uv lock          # first run or after dependency changes
uv run pytest -q
docker compose config
```

### Run services (Phase 1)

```bash
docker compose up -d
curl http://127.0.0.1:8080/healthz   # control-plane
curl http://127.0.0.1:8081/healthz   # model-gateway
```

| Service | Port | Phase 1 |
|---------|------|---------|
| postgres | 5432 (internal) | pgvector Postgres 16 |
| control-plane | 8080 | `GET /healthz` |
| model-gateway | 8081 | `GET /healthz` |

## Environment variables

| Variable | Service | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | control-plane, model-gateway | Postgres connection string |
| `PLATFORM_JWT_SECRET` | control-plane, model-gateway | JWT signing secret (Phase 2+) |
| `ADMIN_TOKEN` | control-plane | Admin API bearer token (Phase 2+) |
| `OPENAI_COMPAT_BASE_URL` | model-gateway | Upstream OpenAI-compatible API base |
| `UPSTREAM_OPENAI_API_KEY` | model-gateway | Upstream provider API key |

## Roadmap

Platform work is split into five phases. Phase 1 exit criteria are met; next is
**Phase 2 — Hard Control** (enrollment, heartbeat, leases, admin revoke, model
gateway enforcement).

See monorepo root [README.md](../README.md) and
[docs/PLATFORM_EXECUTION_PLAN.md](../docs/PLATFORM_EXECUTION_PLAN.md) for the
full specification.
