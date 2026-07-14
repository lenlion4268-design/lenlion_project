# Lenlion Agent — 本地部署与云端数据库

Lenlion Agent **在本机运行**（CLI、Web Chat、Gateway、Cron），会话、配置与密钥通过 **`DATABASE_URL` 连接云端 Postgres**。Agent 不再提供 Docker 容器部署路径；云端数据库由 **`lenlion_platform`** 栈或托管 Postgres 提供。

所有命令均在 **`lenlion_agent/`** 目录下执行。

---

## 1. 架构

```
┌─────────────────────────────────────────────────────────────┐
│  本机（开发者 / 用户机器）                                      │
│  lenlion / lenlion dashboard / lenlion gateway              │
│  ~/.hermes/  → 技能、日志、文件缓存（本地文件）                  │
└───────────────────────────┬─────────────────────────────────┘
                            │ DATABASE_URL（TLS 推荐）
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  云端 Postgres（lenlion_platform 或托管服务）                   │
│  sessions / messages / platform_config / platform_secrets     │
│  + 平台控制表（tenants / agents / leases / …）               │
└─────────────────────────────────────────────────────────────┘
```

| 存储 | 位置 | 内容 |
|------|------|------|
| **本地** `~/.hermes/` | 本机磁盘 | 技能、日志、缓存、临时文件 |
| **云端 Postgres** | `DATABASE_URL` | 会话、消息、Web 配置、密钥、平台控制数据 |

未设置 `DATABASE_URL` 时，Agent 回退到本机 SQLite（`~/.hermes/state.db`）与文件配置，**不适合**与云端 Platform 联调。

---

## 2. 前置条件

| 依赖 | 说明 |
|------|------|
| Python 3.11 – 3.13 | 见 `pyproject.toml` |
| Node.js / npm | 仅在前端开发或重建 Web UI 时需要 |
| 云端 Postgres | 见 §3 |
| 模型 API Key | 托管模式经 Platform 网关；独立模式写入 `~/.hermes/.env` |

---

## 3. 准备云端数据库

### 方式 A：lenlion_platform 本地/云端 Compose（开发推荐）

在部署 Platform 的机器上启动 Postgres（含 pgvector）：

```bash
cd lenlion_platform
docker compose up -d postgres
```

将 **Agent 与会话相关的 schema** 应用到同一数据库（若 Platform 栈尚未包含 agent 表）：

```bash
# 从本机执行，替换为实际连接串
export DATABASE_URL="postgresql://lenlion:lenlion@<platform-host>:5432/lenlion"

psql "$DATABASE_URL" -f lenlion_agent/docker/postgres/init.sql
psql "$DATABASE_URL" -f lenlion_platform/db/init.sql
```

Platform Compose 默认仅挂载 `lenlion_platform/db/init.sql`；**agent 表需单独执行** `lenlion_agent/docker/postgres/init.sql`（同库共存，见 [lenlion_platform/README.md](../lenlion_platform/README.md)）。

### 方式 B：托管 Postgres（Neon、RDS、Cloud SQL 等）

1. 创建数据库与用户，启用 TLS。
2. 依次执行上述两个 `init.sql`。
3. 将连接串写入本机 `~/.hermes/.env`：

```bash
DATABASE_URL=postgresql://user:pass@host:5432/lenlion?sslmode=require
```

---

## 4. 本机安装与首次配置

```bash
cd lenlion_agent

python3 -m venv .venv
source .venv/bin/activate

pip install -e ".[cli,web,mcp,cron,postgres]"
lenlion setup
lenlion doctor
```

在 `~/.hermes/.env` 中确保包含 `DATABASE_URL`（以及非托管模式下的模型 API Key）。

中文界面：

```yaml
# ~/.hermes/config.yaml
display:
  language: zh
```

---

## 5. 日常使用

```bash
source .venv/bin/activate

lenlion              # 终端 CLI
lenlion dashboard    # Web 聊天，默认 http://127.0.0.1:9119
lenlion gateway      # 消息网关（按需）
lenlion cron list    # 定时任务
```

### 构建 Web 前端（可选）

预构建产物已包含在 `hermes_cli/web_dist/`。从源码构建：

```bash
cd web && npm install && npm run build
```

---

## 6. 配置与密钥（DATABASE_URL 模式）

设置 `DATABASE_URL` 后：

| 数据 | 后端 |
|------|------|
| 会话 / 消息 | Postgres `sessions` / `messages` |
| Web 配置 | Postgres `platform_config` |
| API 密钥 | Postgres `platform_secrets` |
| 技能 / 日志 | 本机 `~/.hermes/` |

Web 配置页保存后从 Postgres 读取；无需在多台本机间同步 `config.yaml` / `.env` 文件（密钥仍仅通过 UI 或 admin 流程写入）。

---

## 7. 远程访问 Web Chat

Dashboard 默认绑定 `127.0.0.1:9119`。从其他机器访问请使用 SSH 隧道或反向代理 + OAuth，**不要**将未鉴权的 dashboard 暴露到公网。

```bash
ssh -L 9119:127.0.0.1:9119 user@your-machine
# 本地浏览器打开 http://127.0.0.1:9119
```

---

## 8. 故障排查

| 现象 | 排查 |
|------|------|
| 会话未写入云端 | `echo $DATABASE_URL`；`lenlion doctor`；检查 Postgres 连通与 schema |
| 配置页保存无效 | 确认 `platform_config` 表存在；检查 DB 用户权限 |
| 仍使用 SQLite | 未导出 `DATABASE_URL` 或 shell 未加载 `.env` |
| SSL 连接失败 | 连接串加 `?sslmode=require`（或云厂商要求参数） |

---

## 9. 已弃用：Agent Docker 部署

以下文件保留供 CI 镜像构建验证或历史参考，**不再作为 Agent 部署方式**：

| 文件 | 说明 |
|------|------|
| `Dockerfile` | CI 冒烟构建（`.github/workflows/docker-build.yml`） |
| `DOCKER.md` | 已弃用，见本文 |
| `scripts/deploy-docker.sh` | 已弃用，执行时会提示 |
| `docker-compose.yml` | 已移除（Agent 不再容器化运行） |

Platform 服务（control-plane、model-gateway、Postgres）仍使用 `lenlion_platform/docker-compose.yml` 部署。

---

## 10. 相关文档

| 文档 | 说明 |
|------|------|
| [README.md](./README.md) | 安装与目录结构 |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | 架构与 Postgres 双后端 |
| [../lenlion_platform/README.md](../lenlion_platform/README.md) | 云端 Platform 与 DB 边界 |
| [../README.md](../README.md) | Monorepo 总览 |
