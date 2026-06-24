# lenlion-project

Lenlion 工作区 monorepo — 汇集 **AI Agent 运行时**、**云端监管平台** 与 **AI 小说创作应用**，共享工程规范与 CI，各子项目独立部署、独立文档。

## 子项目

| 目录 | 说明 | 版本 | 文档 |
|------|------|------|------|
| [`lenlion_agent/`](./lenlion_agent/) | 本地 AI Agent 运行时（CLI / Web / Gateway / Cron），基于 [Hermes Agent](https://github.com/NousResearch/hermes-agent) 定制 | `v0.5.0` | [README](./lenlion_agent/README.md) · [部署](./lenlion_agent/DEPLOYMENT.md) · [架构](./lenlion_agent/ARCHITECTURE.md) |
| [`lenlion_platform/`](./lenlion_platform/) | 云端控制平面与 OpenAI 兼容模型网关（enrollment、租约、policy 强制、revoke） | `v0.5.0` | [README](./lenlion_platform/README.md) |
| [`Novel_Generator/`](./Novel_Generator/) | AI 小说自动生成平台 — 本地优先的单作者创作工作台（Next.js + FastAPI） | API/Web `v0.1.0` | [README](./Novel_Generator/README.md) |

## 整体关系

```
┌─────────────────────────────────────────────────────────────┐
│                     lenlion-project                         │
├─────────────────┬─────────────────────┬─────────────────────┤
│  lenlion_agent  │  lenlion_platform   │  Novel_Generator    │
│  （本机运行）    │  （云端 Compose）    │  （独立本地应用）    │
└────────┬────────┴──────────┬──────────┴─────────────────────┘
         │                   │
         │    DATABASE_URL   │  enrollment / heartbeat /
         └──────────────────►│  model gateway / revoke
                             │
                    共用 Postgres（Agent + Platform）
```

- **Agent + Platform** 构成 Lenlion 监管闭环：Agent 在本机执行，Platform 在云端签发租约并在模型网关强制策略；两者可共用同一 Postgres 实例（schema 分别由各自 `init.sql` / 迁移初始化）。
- **Novel Generator** 为独立应用，使用本地 `novel_generator` 数据库，与 Agent/Platform 无运行时耦合；后续可通过 API 或 MCP 与 Agent 集成。

## 仓库结构

```
lenlion-project/
├── .github/workflows/     # CI（测试、lint、PyPI 发布、安全扫描等）
├── docs/                  # 平台总规格与分阶段实施计划
├── lenlion_agent/         # Python 包 lenlion-agent
├── lenlion_platform/      # Python 包 lenlion-platform
└── Novel_Generator/       # apps/api（FastAPI）+ apps/web（Next.js）
```

## 快速开始

各子项目环境要求与启动步骤不同，请进入对应目录阅读 README：

```bash
# Agent — 本机 Python，会话/配置经 DATABASE_URL 写入云端 Postgres
cd lenlion_agent && pip install -e ".[cli,web,mcp,cron,postgres]" && lenlion setup

# Platform — 云端 Postgres + control-plane + model-gateway
cd lenlion_platform && docker compose up -d && uv run pytest -q

# Novel Generator — 本地 Postgres + API + Web
cd Novel_Generator && ./scripts/setup-db.sh && ./scripts/dev.sh
```

## 平台路线图

Lenlion Platform 按阶段交付，规格见 [docs/PLATFORM_EXECUTION_PLAN.md](./docs/PLATFORM_EXECUTION_PLAN.md)：

| 阶段 | 内容 | 状态 |
|------|------|------|
| Phase 1 | 包骨架、DB 边界、健康检查 | ✅ |
| Phase 2 | enrollment、租约 JWT、模型网关强制、revoke | ✅ 当前 |
| Phase 3 | `lenlion_edge` 插件、云端审批、审计上报 | 待实施 |
| Phase 4 | 会话租户元数据、技能/知识注册表 | 待实施 |
| Phase 5 | Admin UI、RLS 与安全加固 | 待实施 |

## 开发与 CI

| 范围 | 常用命令 |
|------|----------|
| Agent | `cd lenlion_agent && uv run pytest` · `uv run ruff check .` |
| Platform | `cd lenlion_platform && uv run pytest -q` |
| Novel Generator | 见 [Novel_Generator/README.md](./Novel_Generator/README.md) |

根目录 [`.github/workflows/`](./.github/workflows/) 主要为 `lenlion_agent` 提供测试、lint、锁文件校验与 PyPI 发布流水线；Platform 与 Novel Generator 的 CI 可随各子项目演进逐步补齐。

## 文档索引

| 文档 | 说明 |
|------|------|
| [lenlion_agent/README.md](./lenlion_agent/README.md) | Agent 安装、命令入口、目录结构 |
| [lenlion_agent/DEPLOYMENT.md](./lenlion_agent/DEPLOYMENT.md) | 本机 Agent + 云端 Postgres |
| [lenlion_agent/ARCHITECTURE.md](./lenlion_agent/ARCHITECTURE.md) | Agent 架构分层与数据流 |
| [lenlion_platform/README.md](./lenlion_platform/README.md) | 控制平面 API、Compose、环境变量 |
| [Novel_Generator/README.md](./Novel_Generator/README.md) | 小说平台 Phase 进度与本地开发 |
| [docs/PLATFORM_EXECUTION_PLAN.md](./docs/PLATFORM_EXECUTION_PLAN.md) | Platform 实施总规格 |
| [lenlion_agent/MIGRATION.md](./lenlion_agent/MIGRATION.md) | 相对上游 Hermes 的定制范围 |

## 许可证

各子项目许可证见对应目录。Agent 沿用上游 Hermes 的 MIT 许可，见 [lenlion_agent/LICENSE](./lenlion_agent/LICENSE)。
