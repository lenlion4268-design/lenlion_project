# Lenlion Agent

**版本：** `0.5.0` · PyPI 包名 `lenlion-agent`

基于 [Hermes Agent](https://github.com/NousResearch/hermes-agent) 核心运行时的 AI Agent 项目。

**部署模型：** 在本机运行（CLI / Web / Gateway），通过 `DATABASE_URL` 连接**云端 Postgres** 存储会话、配置与密钥。不提供 Agent 容器化部署。

## 能力概览

- **CLI** — 终端交互式 Agent（prompt_toolkit）
- **Web Dashboard** — React 19 浏览器管理平台（`lenlion dashboard`）
- **Gateway** — 多平台消息接入（Telegram、Discord、Slack、微信、飞书等）
- **Tools & Skills** — 终端、文件、浏览器、搜索、委派子 Agent 等
- **Cron** — 自然语言定时任务
- **Plugins** — 内存后端、模型提供方等可插拔扩展

## 安装

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[cli,web,mcp,cron,postgres]"
lenlion setup
```

**Python 3.11 – 3.13**（见 `pyproject.toml`）。

在 `~/.hermes/.env` 中配置云端数据库：

```bash
DATABASE_URL=postgresql://user:pass@your-cloud-host:5432/lenlion?sslmode=require
```

首次建库需执行 schema（与 Platform 同库时先 agent、后 platform）：

```bash
psql "$DATABASE_URL" -f docker/postgres/init.sql
psql "$DATABASE_URL" -f ../lenlion_platform/db/init.sql
```

详见 **[DEPLOYMENT.md](./DEPLOYMENT.md)** 与 [../lenlion_platform/README.md](../lenlion_platform/README.md)。

## 使用

```bash
lenlion              # 经典 CLI
lenlion dashboard    # Web 聊天界面（默认 http://127.0.0.1:9119）
lenlion gateway      # 消息网关
lenlion cron list    # 定时任务
lenlion doctor       # 环境检查
```

### 构建 Web 前端

```bash
cd web
npm install
npm run build   # 输出到 hermes_cli/web_dist/
```

| 存储 | 位置 |
|------|------|
| 技能、日志、缓存 | 本机 `~/.hermes/` |
| 会话、消息、配置、密钥 | 云端 Postgres（`DATABASE_URL`） |

## 目录结构

```
lenlion_agent/
├── DEPLOYMENT.md     # 本地部署 + 云端数据库
├── docker/postgres/  # Agent schema（应用到云端库）
├── run_agent.py      # Agent 核心循环
├── hermes_cli/       # CLI + FastAPI Web 服务
├── gateway/          # 消息网关
├── web/              # React 19 管理平台前端
├── tui_gateway/      # WebSocket JSON-RPC 聊天后端
├── agent/ tools/ plugins/ skills/ cron/ tests/
└── ...
```

## 文档

- [DEPLOYMENT.md](./DEPLOYMENT.md) — 本机运行 + 云端 `DATABASE_URL`
- [ARCHITECTURE.md](./ARCHITECTURE.md) — 架构与 Postgres 双后端
- [../lenlion_platform/README.md](../lenlion_platform/README.md) — 云端 Platform 与数据库
- [MIGRATION.md](./MIGRATION.md) — 相对上游 Hermes 的定制范围

## 中文界面

```yaml
# ~/.hermes/config.yaml
display:
  language: zh
```

## 许可证

MIT — 见 [LICENSE](./LICENSE)。
