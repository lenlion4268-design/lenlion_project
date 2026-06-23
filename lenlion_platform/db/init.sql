-- Lenlion Platform control-plane schema.
--
-- Database boundary: co-located with lenlion_agent session/config tables in the
-- same Postgres database (same instance, same DB name). Agent-owned tables
-- (sessions, messages, platform_config, platform_secrets, schema_version) are
-- created by lenlion_agent/docker/postgres/init.sql and are intentionally NOT
-- recreated here.
--
-- Platform migration marker uses platform_schema_version (not schema_version)
-- so agent and platform schema ownership stay independent.

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS platform_schema_version (
    version INTEGER NOT NULL
);

INSERT INTO platform_schema_version (version)
SELECT 1
WHERE NOT EXISTS (SELECT 1 FROM platform_schema_version);

CREATE TABLE IF NOT EXISTS tenants (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(id),
    email TEXT NOT NULL,
    role TEXT NOT NULL,
    created_at BIGINT NOT NULL,
    UNIQUE (tenant_id, email)
);

CREATE TABLE IF NOT EXISTS enrollment_tokens (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(id),
    token_hash TEXT NOT NULL,
    expires_at BIGINT NOT NULL,
    used_at BIGINT,
    created_at BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(id),
    name TEXT NOT NULL,
    hostname TEXT NOT NULL,
    version TEXT NOT NULL,
    node_credential_hash TEXT NOT NULL,
    status TEXT NOT NULL,
    capabilities JSONB NOT NULL DEFAULT '{}'::jsonb,
    last_heartbeat BIGINT,
    revoked_at BIGINT,
    created_at BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS policies (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(id),
    scope TEXT NOT NULL,
    target_id TEXT NOT NULL,
    etag TEXT NOT NULL,
    policy JSONB NOT NULL,
    updated_at BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS leases (
    jti TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(id),
    agent_id TEXT NOT NULL REFERENCES agents(id),
    policy_etag TEXT NOT NULL,
    issued_at BIGINT NOT NULL,
    expires_at BIGINT NOT NULL,
    revoked_at BIGINT
);

CREATE TABLE IF NOT EXISTS approvals (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(id),
    agent_id TEXT NOT NULL REFERENCES agents(id),
    session_id TEXT NOT NULL,
    tool TEXT NOT NULL,
    args_digest TEXT NOT NULL,
    decision TEXT NOT NULL,
    decided_by TEXT NOT NULL,
    approval_token_jti TEXT,
    reason TEXT NOT NULL,
    created_at BIGINT NOT NULL,
    consumed_at BIGINT
);

CREATE TABLE IF NOT EXISTS audit_events (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(id),
    agent_id TEXT,
    session_id TEXT,
    kind TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS skills (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(id),
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    content TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    updated_at BIGINT NOT NULL,
    UNIQUE (tenant_id, name)
);

CREATE TABLE IF NOT EXISTS kb_documents (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(id),
    source TEXT NOT NULL,
    chunk TEXT NOT NULL,
    embedding vector(1536),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS model_usage (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(id),
    agent_id TEXT NOT NULL REFERENCES agents(id),
    session_id TEXT,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    cache_read_tokens INTEGER NOT NULL DEFAULT 0,
    cache_write_tokens INTEGER NOT NULL DEFAULT 0,
    estimated_cost_usd DOUBLE PRECISION,
    created_at BIGINT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_agents_tenant ON agents(tenant_id);
CREATE INDEX IF NOT EXISTS idx_leases_agent_expires ON leases(agent_id, expires_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_tenant_created ON audit_events(tenant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_usage_tenant_created ON model_usage(tenant_id, created_at DESC);
