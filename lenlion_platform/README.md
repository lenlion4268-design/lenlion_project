# Lenlion Platform

**版本：** `0.1.0` · PyPI 包名 `lenlion-platform`

Lenlion 云端控制平面与模型网关，与 **本机运行的** [Lenlion Agent](../lenlion_agent/README.md) 配合使用。

**当前进度：** Phase 1 完成（包骨架、DB 层、schema 边界、健康检查、Docker Compose）。Phase 2+ 将实现 enrollment、租约、admin revoke、模型网关强制。

## 部署分工

| 组件 | 运行位置 |
|------|----------|
| Lenlion Agent | **本机**（`lenlion dashboard` 等） |
| Postgres / control-plane / model-gateway | **云端**（本 compose） |

Agent 通过 `DATABASE_URL` 连接同一 Postgres。建库后须依次执行：

```bash
export DATABASE_URL="postgresql://lenlion:lenlion@127.0.0.1:5432/lenlion"
psql "$DATABASE_URL" -f ../lenlion_agent/docker/postgres/init.sql   # agent 表
psql "$DATABASE_URL" -f db/init.sql                                 # platform 表
```

## 数据库边界

**同 Postgres 实例、同 database、表共存。**

| 归属 | 迁移标记 | 主要表 |
|------|----------|--------|
| `lenlion_agent` | `schema_version` | sessions, messages, platform_config, platform_secrets |
| `lenlion_platform` | `platform_schema_version` | tenants, agents, leases, policies, approvals, … |

`db/init.sql` **不会** 重建 agent 所属表。

## 本地开发

```bash
cd lenlion_platform
uv lock
uv run pytest -q
docker compose up -d
curl http://127.0.0.1:8080/healthz   # control-plane
curl http://127.0.0.1:8081/healthz   # model-gateway
```

| 服务 | 端口 | Phase 1 |
|------|------|---------|
| postgres | 5432 | pgvector Postgres 16 |
| control-plane | 8080 | `GET /healthz` |
| model-gateway | 8081 | `GET /healthz` |

## 环境变量

| 变量 | 用途 |
|------|------|
| `DATABASE_URL` | Postgres 连接串 |
| `PLATFORM_JWT_SECRET` | JWT 签名（Phase 2+） |
| `ADMIN_TOKEN` | Admin API（Phase 2+） |
| `OPENAI_COMPAT_BASE_URL` | 上游 OpenAI 兼容 API |
| `UPSTREAM_OPENAI_API_KEY` | 上游 API Key |

## 路线图

五阶段实施，Phase 1 已验收；下一步 **Phase 2 — Hard Control**（enrollment → gateway → revoke 冒烟）。

- 总规格：[docs/PLATFORM_EXECUTION_PLAN.md](../docs/PLATFORM_EXECUTION_PLAN.md)
- Monorepo 入口：[../README.md](../README.md)
