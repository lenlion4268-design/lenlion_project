# Novel Generator

**版本：** API `0.8.0` · Web `0.8.0`

AI 小说自动生成平台 — **本地优先**的单作者创作工作台，位于 [lenlion-project](../README.md) monorepo 的 `Novel_Generator/` 目录。

**当前进度：** Phase 10 — 设置中心（模型配置、技能库、个人信息）；素材库独立于创作项目。

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | Next.js 16 · React 19 · TypeScript · Tailwind CSS 4 |
| 后端 | FastAPI · SQLAlchemy 2 · Alembic · Pydantic Settings |
| 数据库 | PostgreSQL（本地，库名 `novel_generator`） |
| 队列 | 线程 / Redis / Celery（生成与文风分析共用） |
| AI | `mock` / OpenAI 兼容 API |
| 文风 | 参考小说上传 → 采样 → 3-pass 分析 → Skill 导出 |

**Python 3.11 – 3.13**（见 `apps/api/pyproject.toml`）。

## 快速开始

```bash
cp .env.example apps/api/.env
cp apps/web/.env.local.example apps/web/.env.local
POSTGRES_PASSWORD=你的密码 ./scripts/setup-db.sh
cd apps/api && alembic upgrade head
```

### 启动 API + Web

```bash
cd apps/api && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000
cd apps/web && npm install && npm run dev
```

工作区侧栏 **素材库 → 文风参考**：上传参考小说（**作者必填**），分析文风后前往 **设置 > 技能库** 管理；章节页可从技能库绑定文风。

顶栏 **设置**：模型配置（PostgreSQL 持久化、即时生效）、技能库、个人信息。

## 环境变量

| 变量 | 说明 |
|------|------|
| `STYLE_SAMPLE_MAX_CHARS` | 采样总字符上限，默认 12000 |
| `STYLE_UPLOAD_MAX_MB` | 上传大小上限（MB），默认 10 |
| `STYLE_ANALYSIS_FORCE_SYNC` | 测试/调试：同步执行文风分析 |

完整列表见 [`.env.example`](./.env.example)。

## 开发与测试

```bash
cd apps/api && pytest -q
cd apps/web && npm run lint
```

## 路线图

| 阶段 | 内容 | 状态 |
|------|------|------|
| Phase 0–8 | 骨架 → Celery → EPUB → 平台发布 | ✅ |
| Phase 9 | 文风解析、作者优先 Skill、独立素材库 | ✅ |
| Phase 10 | 设置中心：模型 / 技能库 / 个人信息 | ✅ 当前 |

## 文档

- [packages/shared/domain-contracts.md](./packages/shared/domain-contracts.md)
- [../README.md](../README.md)

**版权提示：** 仅上传您有权使用的参考文本。
