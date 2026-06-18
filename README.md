# lenlion-project

Lenlion 工作区 monorepo，当前包含 **Lenlion Agent** —— 基于 [Hermes Agent](https://github.com/NousResearch/hermes-agent) 核心运行时的独立 AI Agent 项目。

Lenlion Agent 是一个 **本地优先（local-first）** 的可插拔 Agent 运行时：终端 CLI、浏览器 Web 聊天、多平台消息网关与定时任务共用同一套 Agent 核心，通过工具、技能与插件扩展能力。

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
├── .github/              # CI 流水线（working-directory: lenlion_agent）
├── ARCHITECTURE.md       # 架构说明
└── lenlion_agent/        # Lenlion Agent 主项目（Python 包 lenlion-agent）
    ├── run_agent.py      # Agent 核心循环
    ├── agent/            # 对话循环、上下文、传输层
    ├── tools/            # 工具实现
    ├── hermes_cli/       # CLI 子命令 + FastAPI Web 服务
    ├── gateway/          # 消息网关
    ├── web/              # Vue 3 聊天前端（构建到 hermes_cli/web_dist/）
    ├── tui_gateway/      # WebSocket JSON-RPC 聊天后端引擎
    ├── cron/             # 调度器
    ├── plugins/          # 内置插件
    ├── skills/           # 内置技能
    └── tests/            # 测试
```

## 环境要求

- **Python** 3.11 – 3.13（见 `lenlion_agent/pyproject.toml`）
- **Node.js / npm** — 仅在前端开发或重新构建 Web UI 时需要

配置与数据目录沿用 Hermes 约定：`~/.hermes/`（`config.yaml`、`.env`、`state.db` 等）。

## 快速开始

```bash
cd lenlion_agent

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -e ".[cli,web,mcp,cron]"
lenlion setup

lenlion              # 终端 CLI
lenlion dashboard    # Web 聊天界面
lenlion doctor       # 检查环境
```

首次使用需在 `~/.hermes/.env` 或 `config.yaml` 中配置模型 API Key（如 OpenAI、Anthropic 等）。详见 [lenlion_agent/README.md](./lenlion_agent/README.md)。

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

本项目 **不提供** 独立的云托管或 Docker 编排；采用 **Python 包 + 本机进程** 部署：

| 层级 | 方式 |
|------|------|
| **分发** | PyPI 包 `lenlion-agent`；打 CalVer tag（`v20*.*.*`）时由 GitHub Actions 发布 |
| **本地开发** | `pip install -e ".[cli,web,mcp,cron]"` |
| **Web UI** | Vue 构建产物内嵌于 wheel，由 `lenlion dashboard`（FastAPI + uvicorn）同进程提供静态文件与 `/api/ws` |
| **默认绑定** | `127.0.0.1:9119`（本机使用）；对外暴露需自行配置反向代理并启用 OAuth 门控 |

相对上游 Hermes，本仓库 **未迁移** Docker / Nix / Electron 桌面端 / 文档站等边缘模块。详见 [lenlion_agent/MIGRATION.md](./lenlion_agent/MIGRATION.md)。

## 开发与测试

所有命令均在 `lenlion_agent/` 目录下执行（CI 亦如此）：

```bash
cd lenlion_agent
source .venv/bin/activate

# 运行测试（与 CI 相同，需 uv）
uv run pytest

# 代码检查
uv run ruff check .
```

## CI

根目录 `.github/workflows/` 在 `lenlion_agent/` 下运行：

- **tests.yml** — 单元与集成测试（6 路分片并行）
- **lint.yml** — Ruff / 格式检查
- **upload_to_pypi.yml** — CalVer tag 触发 PyPI 发布
- **uv-lockfile-check.yml** — 锁文件一致性
- **osv-scanner.yml** / **supply-chain-audit.yml** — 供应链安全扫描

## 文档

| 文档 | 说明 |
|------|------|
| [lenlion_agent/README.md](./lenlion_agent/README.md) | 安装、使用、目录结构 |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | 架构分层、模块职责、数据流 |
| [lenlion_agent/MIGRATION.md](./lenlion_agent/MIGRATION.md) | 相对上游 Hermes 的迁移与定制范围 |
| [lenlion_agent/README.hermes-upstream.md](./lenlion_agent/README.hermes-upstream.md) | 上游 Hermes 完整文档 |
| [lenlion_agent/README.zh-CN.md](./lenlion_agent/README.zh-CN.md) | 上游中文文档 |

## 许可证

MIT — 与上游 Hermes Agent 相同。见 [lenlion_agent/LICENSE](./lenlion_agent/LICENSE)。
