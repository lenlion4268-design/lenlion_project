# lenlion-project

Lenlion 工作区 monorepo，包含：

- **Lenlion Agent** `v0.5.0`（`lenlion_agent/`）—— 基于 [Hermes Agent](https://github.com/NousResearch/hermes-agent) 的本地 AI Agent 运行时（**本机运行**）
- **Lenlion Platform** `v0.5.0`（`lenlion_platform/`）—— 云端控制平面与模型网关（Phase 2：enrollment、租约、网关强制、revoke）

Agent 在本机运行 CLI / Web Chat / Gateway / Cron；会话与配置经 **`DATABASE_URL`** 写入云端 Postgres。Platform 托管数据库与控制平面服务（Phase 3：本地 edge 插件与云端审批待实施）。

## 能力概览

| 入口 | 命令 | 说明 |
|------|------|------|
| **CLI** | `lenlion` | 终端交互式 Agent（prompt_toolkit） |
| **Web Chat** | `lenlion dashboard` | Vue 3 浏览器聊天界面，默认 `http://127.0.0.1:9119` |
| **Gateway** | `lenlion gateway` | 多平台消息接入（Telegram、Discord、Slack、微信、飞书等） |
| **Cron** | `lenlion cron` | 自然语言定时任务 |
| **诊断** | `lenlion doctor` | 环境与依赖检查 |

其他能力：终端 / 文件 / 浏览器 / 搜索工具、子 Agent 委派、MCP 集成、可插拔内存后端与模型提供方。

## 仓库结构

```
lenlion-project/
├── .github/              # CI 流水线
├── lenlion_agent/        # Lenlion Agent 主项目（Python 包 lenlion-agent，本机运行）
│   ├── ARCHITECTURE.md   # 架构说明
│   ├── DEPLOYMENT.md     # 本地部署 + 云端 DATABASE_URL
│   ├── docker/postgres/  # Agent 会话 / 配置 schema（应用到云端库）
│   ├── run_agent.py      # Agent 核心循环
│   ├── agent/            # 对话循环、上下文、传输层
│   ├── tools/            # 工具实现
│   ├── hermes_cli/       # CLI 子命令 + FastAPI Web 服务
│   ├── gateway/          # 消息网关
│   ├── web/              # Vue 3 聊天前端（构建到 hermes_cli/web_dist/）
│   ├── tui_gateway/      # WebSocket JSON-RPC 聊天后端引擎
│   ├── cron/             # 调度器
│   ├── plugins/          # 内置插件
│   ├── skills/           # 内置技能
│   └── tests/            # 测试
└── lenlion_platform/     # 云端控制平面（Python 包 lenlion-platform）
    ├── control_plane/    # enrollment / lease / approval API
    ├── model_gateway/    # OpenAI 兼容模型网关（policy 强制）
    ├── db/init.sql       # 平台控制表（与 agent 表同库共存）
    ├── docker-compose.yml
    └── tests/
```

## 环境要求

- **Python** 3.11 – 3.13（见 `lenlion_agent/pyproject.toml`）
- **Node.js / npm** — 仅在前端开发或重新构建 Web UI 时需要

配置与数据目录沿用 Hermes 约定：`~/.hermes/`（技能、日志、缓存等本地文件）。设置 **`DATABASE_URL`** 后会话、Web 配置与密钥存入云端 Postgres。

## 快速开始

```bash
cd lenlion_agent

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -e ".[cli,web,mcp,cron,postgres]"
# 在 ~/.hermes/.env 中设置 DATABASE_URL（云端 Postgres）
lenlion setup

lenlion              # 终端 CLI
lenlion dashboard    # Web 聊天界面
lenlion doctor       # 检查环境
```

云端数据库准备见 **[lenlion_agent/DEPLOYMENT.md](./lenlion_agent/DEPLOYMENT.md)**。首次使用需在 `~/.hermes/.env` 或 Web 配置页中配置 `DATABASE_URL` 与模型 API Key。详见 [lenlion_agent/README.md](./lenlion_agent/README.md)。

### 构建 Web 前端

预构建的静态资源已打包在 `hermes_cli/web_dist/`。如需从源码构建：

```bash
cd lenlion_agent/web
npm install
npm run build    # 输出到 ../hermes_cli/web_dist/
```

`lenlion dashboard` 在检测到 dist 过期时会自动尝试构建（需本机安装 Node.js）。

### 中文界面

在 `~/.hermes/config.yaml` 中设置：

```yaml
display:
  language: zh
```

## 部署方式

**Agent 在本机运行，数据在云端 Postgres。**

| 组件 | 部署位置 | 说明 |
|------|----------|------|
| **Lenlion Agent** | 本机 Python 包 | `pip install -e ".[cli,web,mcp,cron,postgres]"` |
| **Postgres** | 云端（Platform 或托管） | 会话、配置、密钥 + 平台控制表 |
| **Lenlion Platform** | 云端 Docker Compose | control-plane、model-gateway（见 `lenlion_platform/`） |

完整步骤见 **[lenlion_agent/DEPLOYMENT.md](./lenlion_agent/DEPLOYMENT.md)**。

```bash
# 1. 云端：Postgres + Platform 服务
cd lenlion_platform
docker compose up -d postgres
export DATABASE_URL="postgresql://lenlion:lenlion@127.0.0.1:5432/lenlion"
psql "$DATABASE_URL" -f ../lenlion_agent/docker/postgres/init.sql
psql "$DATABASE_URL" -f db/init.sql
docker compose up -d   # control-plane :8080, model-gateway :8081

# 2. 本机：Agent
cd ../lenlion_agent
pip install -e ".[cli,web,mcp,cron,postgres]"
# ~/.hermes/.env → 同上 DATABASE_URL
lenlion setup && lenlion dashboard
```

| 层级 | 方式 |
|------|------|
| **分发** | PyPI 包 `lenlion-agent`；CalVer tag 触发 PyPI 发布 |
| **Web UI** | Vue 构建产物内嵌于 wheel，由 `lenlion dashboard` 提供 |
| **默认绑定** | `127.0.0.1:9119`；远程访问请用 SSH 隧道或反向代理 + OAuth |

## 开发与测试

### Agent（`lenlion_agent/`）

所有 Agent 命令与 CI 均在 `lenlion_agent/` 下执行：

```bash
cd lenlion_agent
source .venv/bin/activate

# 运行测试（与 CI 相同，需 uv）
uv run pytest

# 代码检查
uv run ruff check .
```

### Platform（`lenlion_platform/`）

Phase 2 提供 enrollment / heartbeat / revoke / 模型网关；Phase 3 将接入 `lenlion_edge` 插件。

```bash
cd lenlion_platform
uv lock          # 首次或依赖变更后
uv run pytest -q
docker compose config
docker compose up -d   # postgres :5432, control-plane :8080, model-gateway :8081
curl http://127.0.0.1:8080/healthz
```

平台与 Agent 共用同一 Postgres 实例时，Agent 表由 `lenlion_agent/docker/postgres/init.sql` 初始化，平台表由 `lenlion_platform/db/init.sql` 追加；迁移标记分别为 `schema_version` 与 `platform_schema_version`。详见 [lenlion_platform/README.md](./lenlion_platform/README.md)。

## CI

根目录 `.github/workflows/` 在 `lenlion_agent/` 下运行：

- **tests.yml** — 单元与集成测试（6 路分片并行）
- **lint.yml** — Ruff / 格式检查
- **upload_to_pypi.yml** — CalVer tag 触发 PyPI 发布
- **uv-lockfile-check.yml** — 锁文件一致性
- **docker-build.yml** — Agent 镜像 CI 冒烟（非部署路径）
- **osv-scanner.yml** / **supply-chain-audit.yml** — 供应链安全扫描

## 文档

| 文档 | 说明 |
|------|------|
| [lenlion_agent/DEPLOYMENT.md](./lenlion_agent/DEPLOYMENT.md) | 本机 Agent + 云端 DATABASE_URL |
| [lenlion_agent/README.md](./lenlion_agent/README.md) | 安装、使用、目录结构 |
| [lenlion_agent/ARCHITECTURE.md](./lenlion_agent/ARCHITECTURE.md) | 架构分层、模块职责、数据流 |
| [lenlion_platform/README.md](./lenlion_platform/README.md) | 平台包说明、DB 边界、本地开发与 Compose |
| [docs/PLATFORM_EXECUTION_PLAN.md](./docs/PLATFORM_EXECUTION_PLAN.md) | 平台实施总规格（Phase 3+ 执行入口） |
| [lenlion_agent/MIGRATION.md](./lenlion_agent/MIGRATION.md) | 相对上游 Hermes 的迁移与定制范围 |
| [lenlion_agent/README.hermes-upstream.md](./lenlion_agent/README.hermes-upstream.md) | 上游 Hermes 完整文档 |
| [lenlion_agent/README.zh-CN.md](./lenlion_agent/README.zh-CN.md) | 上游中文文档 |

## 许可证

MIT — 与上游 Hermes Agent 相同。见 [lenlion_agent/LICENSE](./lenlion_agent/LICENSE)。
