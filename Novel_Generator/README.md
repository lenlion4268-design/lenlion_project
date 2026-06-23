# Novel Generator

**版本：** API `0.1.0` · Web `0.1.0`

AI 小说自动生成平台 — **本地优先**的单作者创作工作台，位于 [lenlion-project](../README.md) monorepo 的 `Novel_Generator/` 目录。

**当前进度：** Phase 0 — 工程骨架、领域枚举、PostgreSQL + Alembic、FastAPI 健康检查、Next.js 首页联调。业务表与 AI 生成流程尚未实现。

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | Next.js 16 · React 19 · TypeScript · Tailwind CSS 4 |
| 后端 | FastAPI · SQLAlchemy 2 · Alembic · Pydantic Settings |
| 数据库 | PostgreSQL（本地，库名 `novel_generator`） |
| AI（Phase 0） | `AI_PROVIDER=mock`，仅占位配置 |

**Python 3.11 – 3.13**（见 `apps/api/pyproject.toml`）。

## 快速开始

所有命令默认在 **`Novel_Generator/`** 目录下执行。

### 1. 环境变量

```bash
cp .env.example apps/api/.env
cp apps/web/.env.local.example apps/web/.env.local
```

| 变量 | 位置 | 说明 |
|------|------|------|
| `DATABASE_URL` | `apps/api/.env` | Postgres 连接串（默认 `novel:novel_password@localhost:5432/novel_generator`） |
| `CORS_ORIGINS` | `apps/api/.env` | 允许的前端源（默认 `http://localhost:3000`） |
| `NEXT_PUBLIC_API_BASE_URL` | `apps/web/.env.local` | 前端调用的 API 根路径（默认 `http://localhost:8000/api`） |

### 2. 初始化数据库

脚本会创建用户/库、安装 API 依赖并执行 `alembic upgrade head`：

```bash
POSTGRES_PASSWORD=你的postgres密码 ./scripts/setup-db.sh
```

若 `psql` 不在 PATH（如 PostgreSQL 18 默认安装路径）：

```bash
PSQL=/Library/PostgreSQL/18/bin/psql \
  POSTGRES_PASSWORD=你的密码 ./scripts/setup-db.sh
```

### 3. 启动后端

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

健康检查：`GET http://localhost:8000/api/health` → `{"status":"ok"}`

### 4. 启动前端

```bash
cd apps/web
npm install
npm run dev
```

浏览器打开 **http://localhost:3000**，首页展示 API 联调状态。

## 开发与测试

```bash
# 后端测试
cd apps/api && source .venv/bin/activate && pytest -q

# 前端 lint
cd apps/web && npm run lint

# 新建数据库迁移（Phase 1+ 有表变更时使用）
cd apps/api && alembic revision -m "describe_change"
cd apps/api && alembic upgrade head
```

## 项目结构

```text
Novel_Generator/
├── apps/
│   ├── api/                 FastAPI 后端
│   │   ├── app/
│   │   │   ├── main.py      应用入口、CORS、/api/health
│   │   │   ├── core/        配置、枚举、数据库、错误类型
│   │   │   └── tests/
│   │   └── alembic/         数据库迁移
│   └── web/                 Next.js 前端
│       ├── app/             App Router 页面
│       └── lib/api.ts       API 客户端
├── packages/
│   └── shared/
│       └── domain-contracts.md   跨端领域枚举与 API 约定
├── scripts/
│   ├── setup-db.sh          一键建库 + 迁移
│   └── init-db.sql          创建 novel 数据库用户
├── .env.example
└── README.md
```

## 领域模型（Phase 0 已定义）

后端枚举见 `apps/api/app/core/enums.py`，前后端约定见 [`packages/shared/domain-contracts.md`](packages/shared/domain-contracts.md)：

- **ProjectMode** — `long` / `short`
- **ConfirmStatus** — 创作资产确认流转（draft → confirmed → locked …）
- **LockStatus** — 锁定状态
- **GenerationJobStatus** — AI 生成任务生命周期

## 与 Lenlion 生态的关系

Novel Generator 为 **独立应用**，使用**本地 Postgres**（`novel_generator` 库），与 `lenlion_agent` / `lenlion_platform` 的云端 `DATABASE_URL` 方案无耦合。后续若需 Agent 辅助写作，可通过 API 或 MCP 集成，不在 Phase 0 范围内。

## 路线图

| 阶段 | 内容 | 状态 |
|------|------|------|
| Phase 0 | 工程骨架、领域约束、健康检查、前后端联调 | ✅ 当前 |
| Phase 1+ | 项目/章节/角色模型、AI 生成流水线、创作工作台 UI | 待实施 |
