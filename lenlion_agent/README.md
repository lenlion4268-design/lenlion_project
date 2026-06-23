# Lenlion Agent

基于 [Hermes Agent](https://github.com/NousResearch/hermes-agent) 核心运行时的独立 AI Agent 项目。

**部署模型：** 在本机运行 Agent（CLI / Web / Gateway），通过 `DATABASE_URL` 连接**云端 Postgres** 存储会话、配置与密钥。不再提供 Agent 容器化部署。

## 能力概览

- **CLI** — 终端交互式 Agent（prompt_toolkit）
- **Web Chat** — Vue 3 浏览器聊天界面（`lenlion dashboard`）
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

在 `~/.hermes/.env` 中配置云端数据库：

```bash
DATABASE_URL=postgresql://user:pass@your-cloud-host:5432/lenlion?sslmode=require
```

Schema 初始化与 Platform 联调见 **[DEPLOYMENT.md](./DEPLOYMENT.md)**。

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

`lenlion dashboard` 会在 dist 过期时自动尝试构建（需本机安装 Node.js/npm）。

- **本地文件：** `~/.hermes/` — 技能、日志、缓存
- **云端 Postgres（`DATABASE_URL`）：** 会话、消息、Web 配置、密钥

## 目录结构

```
lenlion_agent/
├── DEPLOYMENT.md     # 本地部署 + 云端数据库（主文档）
├── docker/postgres/  # Agent schema（应用到云端库）
├── run_agent.py      # Agent 核心循环
├── model_tools.py    # 工具编排
├── toolsets.py       # 工具集
├── cli.py            # CLI 编排
├── agent/            # Agent 内部模块
├── tools/            # 工具实现
├── hermes_cli/       # CLI 子命令 + FastAPI Web 服务
├── gateway/          # 消息网关
├── web/              # Vue 3 聊天前端
├── tui_gateway/      # WebSocket JSON-RPC 聊天后端引擎
├── cron/             # 调度器
├── plugins/          # 内置插件
├── skills/           # 内置技能
├── tests/            # 测试
└── ...
```

CI 配置位于 monorepo 根目录 `.github/`（`working-directory: lenlion_agent`）。

## 文档

- [DEPLOYMENT.md](./DEPLOYMENT.md) — 本机运行 + 云端 `DATABASE_URL`
- [ARCHITECTURE.md](./ARCHITECTURE.md) — 架构与 Postgres 双后端
- [MIGRATION.md](./MIGRATION.md) — 迁移范围与定制说明
- [README.hermes-upstream.md](./README.hermes-upstream.md) — 上游 Hermes 完整文档
- [README.zh-CN.md](./README.zh-CN.md) — 上游中文文档

## 中文界面

在 `~/.hermes/config.yaml` 中设置：

```yaml
display:
  language: zh
```

## 许可证

MIT — 与上游 Hermes Agent 相同。见 [LICENSE](./LICENSE)。
