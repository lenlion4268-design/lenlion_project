# Lenlion Platform

**版本：** `0.5.0` · PyPI 包名 `lenlion-platform`

Lenlion 云端控制平面与模型网关，与 **本机运行的** [Lenlion Agent](../lenlion_agent/README.md) 配合使用。

**当前进度：** Phase 2 完成 — enrollment、heartbeat、租约 JWT、admin revoke、模型网关强制（policy fail-closed）。

## 能力（Phase 2）

| 接口 | 说明 |
|------|------|
| `POST /admin/enrollment-tokens` | Admin 创建一次性 enrollment token |
| `POST /agents/register` | Agent 注册，返回 `node_credential`（仅一次） |
| `POST /agents/heartbeat` | 续租，返回 `agent_token` + `EdgePolicy` |
| `GET /admin/agents` | Admin 列出 agents（tenant 过滤 + 分页） |
| `GET /admin/audit-events` | Admin 审计事件列表 |
| `GET /admin/approvals` | Admin 审批记录列表 |
| `POST /admin/agents/{id}/revoke` | 撤销 agent 及活跃 lease |
| `GET /v1/models` | 模型网关（需 `agent_token`） |
| `POST /v1/chat/completions` | OpenAI 兼容代理（policy 校验 + 上游转发） |

注册助手：

```bash
python scripts/enroll_agent.py \
  --base-url http://127.0.0.1:8080 \
  --name local-dev \
  --enrollment-token "$ENROLLMENT_TOKEN"
```

## 部署分工

| 组件 | 运行位置 |
|------|----------|
| Lenlion Agent | **本机** |
| Postgres / control-plane / model-gateway | **云端**（本 compose） |

Agent 通过 `DATABASE_URL` 连接同一 Postgres。建库后须依次执行：

```bash
export DATABASE_URL="postgresql://lenlion:lenlion@127.0.0.1:5432/lenlion"
psql "$DATABASE_URL" -f ../lenlion_agent/docker/postgres/init.sql
psql "$DATABASE_URL" -f db/init.sql
```

## 硬控制冒烟（本地）

```bash
docker compose up -d postgres control-plane model-gateway

# 创建 enrollment token
curl -s -X POST http://127.0.0.1:8080/admin/enrollment-tokens \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"dev-tenant"}'

# 注册 + 写 ~/.hermes 配置
python scripts/enroll_agent.py --name local-dev --enrollment-token "$TOKEN"

# 心跳取 agent_token 后调网关；revoke 后应 401/403
```

## 环境变量

| 变量 | 服务 | 用途 |
|------|------|------|
| `DATABASE_URL` | control-plane, model-gateway | Postgres |
| `PLATFORM_JWT_SECRET` | 两者 | JWT HS256 签名 |
| `ADMIN_TOKEN` | control-plane | Admin API |
| `OPENAI_COMPAT_BASE_URL` | model-gateway | 上游 OpenAI 兼容 API |
| `UPSTREAM_OPENAI_API_KEY` | model-gateway | 上游 Key |

## Admin UI（React）

构建并挂载到 control-plane `/admin-ui/`：

```bash
cd lenlion_platform/web
npm ci
npm run build
cd ..
uv run pytest tests/test_admin_api.py tests/test_static_ui.py -q
docker compose up -d control-plane
# 浏览器打开 http://127.0.0.1:8080/admin-ui/
```

Admin token 仅在浏览器内存中使用，不会写入 localStorage。

## 开发与测试

```bash
cd lenlion_platform
uv lock
uv run pytest -q -m "not postgres_smoke"
docker compose up -d postgres
# 真实 dual-init smoke（需 pgvector Postgres）：
export DATABASE_URL="postgresql://lenlion:lenlion@127.0.0.1:5432/lenlion"
LENLION_PLATFORM_POSTGRES_SMOKE=1 uv run pytest -q -m postgres_smoke
```

CI：根目录 [`.github/workflows/platform-tests.yml`](../.github/workflows/platform-tests.yml)。

## 路线图

| 阶段 | 状态 |
|------|------|
| Phase 1 — Foundation | ✅ |
| Phase 2 — Hard Control | ✅ 当前 |
| Phase 3 — Edge Runtime | 待实施 |

- 总规格：[docs/PLATFORM_EXECUTION_PLAN.md](../docs/PLATFORM_EXECUTION_PLAN.md)
- Monorepo：[../README.md](../README.md)
