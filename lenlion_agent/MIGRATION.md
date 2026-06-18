# Lenlion Agent 迁移说明

本目录是由 [hermes-agent](https://github.com/NousResearch/hermes-agent) 核心运行时 fork 而来的**独立项目**。

**迁移时间：** 2026-06-18  
**源路径：** `/Users/lenlion/workspace/study/hermes-agent`  
**包名：** `lenlion-agent`（PyPI / pip 安装名）

## 已迁移（核心）

| 模块 | 说明 |
|------|------|
| `run_agent.py` / `agent/` | Agent 对话循环与内部逻辑 |
| `model_tools.py` / `tools/` | 工具注册与实现 |
| `toolsets.py` | 工具集定义 |
| `cli.py` / `hermes_cli/` | CLI 入口与子命令 + FastAPI Dashboard |
| `gateway/` | 消息网关（Telegram、Discord、Slack 等） |
| `web/` | Vue 3 Web 聊天前端（构建到 `hermes_cli/web_dist/`） |
| `tui_gateway/` | WebSocket JSON-RPC 聊天后端引擎（非终端 UI） |
| `cron/` | 定时任务调度 |
| `plugins/` | 内置插件（memory、model-providers 等） |
| `providers/` | 推理后端 |
| `skills/` | 内置技能 |
| `locales/` | 多语言静态消息 |
| `tests/` / `scripts/` | 测试与脚本 |
| `optional-mcps/` | 可选 MCP 目录 |
| `.github/`（monorepo 根目录） | CI 流水线（已裁剪为仅核心模块） |

## 已移除（相对上游 Hermes）

| 模块 | 说明 |
|------|------|
| `ui-tui/` | Ink/React 终端 TUI（已由 Vue Web Chat 替代） |
| `pty_bridge.py` | Dashboard PTY 嵌入层 |
| `/api/pty`、`/api/pub`、`/api/events` | TUI 嵌入相关 WebSocket 端点 |
| `lenlion --tui` | CLI TUI 启动路径 |

## 未迁移（边缘 / 非核心）

| 模块 | 说明 |
|------|------|
| `website/` | Docusaurus 文档站 |
| `apps/desktop/` | Electron 桌面应用 |
| 上游 React `web/` 全功能 Dashboard | 本仓库仅实现 chat-only Vue SPA |
| `optional-skills/` | 可选重型技能包 |
| `acp_adapter/` | VS Code / Zed ACP 集成 |
| `docker/` / `nix/` | 容器与 Nix 打包 |
| `docs/` / `plans/` | 内部文档与计划 |

如需上述模块，可从源仓库单独复制或 submodule 引入。

## 快速开始

```bash
cd lenlion_agent

python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[cli,web,mcp,cron]"
lenlion setup
lenlion dashboard
```

构建 Web 前端（可选，dashboard 也会自动尝试）：

```bash
cd web && npm install && npm run build
```

## 配置与数据

用户配置仍使用 `~/.hermes/`（`config.yaml`、`.env`、sessions 等），与上游 Hermes 兼容。CLI 命令为 `lenlion`。

## 已完成的定制

1. ✅ `pyproject.toml` 项目名改为 `lenlion-agent`，版本重置为 `0.1.0`
2. ✅ 独立 CI（monorepo 根目录 `.github/`，已移除 website、docker、desktop 等 workflow）
3. ✅ CLI 命令改为 `lenlion`（配置目录仍为 `~/.hermes/`）
4. ✅ 入口文档改为 [README.md](./README.md)
5. ✅ skills、locales、插件文档与代码内用户提示中的 CLI 命令已统一为 `lenlion`
6. ✅ 移除 Ink TUI，新增 Vue 3 Web Chat（`/api/ws` + `tui_gateway`）

## 后续定制建议

1. 按需裁剪 `gateway/platforms/` 中不需要的平台适配器
2. 在 `skills/` 中添加业务专属技能
3. 通过 `~/.hermes/plugins/` 扩展能力，避免修改核心
4. 扩展 `web/` 接入 REST 管理页（配置、会话列表等）

## 与上游同步

```bash
rsync -av --exclude='.git' --exclude='.venv' \
  /Users/lenlion/workspace/study/hermes-agent/agent/ ./agent/
# ... 其他目录同理
```
