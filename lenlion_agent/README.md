# Lenlion Agent

基于 [Hermes Agent](https://github.com/NousResearch/hermes-agent) 核心运行时的独立 AI Agent 项目。

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
pip install -e ".[cli,web,mcp,cron]"
lenlion setup
```

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

配置与数据目录仍为 `~/.hermes/`（与上游 Hermes 兼容）。

## Docker 部署

容器化运行见 monorepo 根目录 **[DOCKER.md](../DOCKER.md)**：

```bash
# 在 lenlion-project/ 根目录
scripts/deploy-docker.sh build && scripts/deploy-docker.sh setup && scripts/deploy-docker.sh up
```

或在 `lenlion_agent/` 下直接 `docker compose up -d`。

## 目录结构

```
lenlion_agent/
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
