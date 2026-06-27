# 跨端领域约束

本文档记录前后端共享的领域状态枚举与 API 约定。后端实现见 `apps/api/app/core/enums.py`。

## 项目模式 (ProjectMode)

| 值 | 说明 |
|---|---|
| `long` | 长篇模式 |
| `short` | 短篇模式 |

## 确认状态 (ConfirmStatus)

创作资产（角色、主题、世界观、大纲等）的确认流转状态。

| 值 | 说明 |
|---|---|
| `draft` | 草稿，作者可编辑 |
| `pending_confirm` | 待确认 |
| `confirmed` | 已确认 |
| `locked` | 已锁定，不可修改 |
| `rejected` | 已驳回 |
| `archived` | 已归档 |

## 锁定状态 (LockStatus)

| 值 | 说明 |
|---|---|
| `unlocked` | 未锁定 |
| `locked` | 已锁定 |

## 生成任务状态 (GenerationJobStatus)

AI 生成任务的生命周期状态。

| 值 | 说明 |
|---|---|
| `queued` | 排队中 |
| `running` | 执行中 |
| `succeeded` | 成功 |
| `failed` | 失败 |
| `cancelled` | 已取消 |

## 项目状态 (ProjectStatus)

| 值 | 说明 |
|---|---|
| `active` | 进行中 |
| `archived` | 已归档 |

## 创作阶段 (ProjectStage)

| 值 | 说明 |
|---|---|
| `characters` | 角色卡 |
| `theme` | 主题题材 |
| `world` | 世界观 |
| `outline` | 大纲 |
| `volumes` | 故事卷 |
| `chapters` | 章节 |

## API 约定

- API 前缀：`/api`
- 健康检查：`GET /api/health` → `{ "status", "queue_backend", "redis_connected", "celery_broker_configured" }`
- 前端通过 `NEXT_PUBLIC_API_BASE_URL` 访问后端（默认 `http://localhost:8000/api`）

### 项目 API

- `POST /api/projects` — 创建项目
- `GET /api/projects` — 项目列表（按 `updated_at` 倒序，支持 `?status=` 筛选）
- `GET /api/projects/{project_id}` — 项目详情
- `PATCH /api/projects/{project_id}` — 更新项目

### 创作资产 API

- `POST /api/projects/{project_id}/character-cards` — 创建角色卡（默认 `confirm_status=draft`）
- `GET /api/projects/{project_id}/character-cards` — 角色卡列表
- `PATCH /api/character-cards/{card_id}` — 更新角色卡
- `PUT /api/projects/{project_id}/theme-profile` — 保存/覆盖主题题材草稿
- `GET /api/projects/{project_id}/theme-profile` — 读取主题题材
- `PUT /api/projects/{project_id}/world-setting` — 保存/覆盖世界观草稿
- `GET /api/projects/{project_id}/world-setting` — 读取世界观
- `POST /api/projects/{project_id}/outlines` — 创建大纲草稿
- `GET /api/projects/{project_id}/outlines` — 大纲列表
- `POST /api/projects/{project_id}/volumes` — 创建故事卷草稿
- `GET /api/projects/{project_id}/volumes` — 故事卷列表

草稿资产不会自动进入下游 AI 生成上下文；确认与锁定流程见 Phase 2。

### 审核 API（Phase 2）

- `POST /api/review/confirm` — 确认资产（draft/pending_confirm → confirmed）
- `POST /api/review/lock` — 锁定资产
- `POST /api/review/reject` — 驳回资产
- `POST /api/review/unlock` — 解锁资产（locked → confirmed）
- `GET /api/projects/{project_id}/readiness/{target_stage}` — 生成准入检查（`outline` / `volumes` / `chapters`）

准入规则：

- 大纲生成：主题、世界观、至少一个核心角色为 confirmed 或 locked
- 故事卷生成：目标大纲为 locked（可传 `?outline_id=`）
- 章节生成：主题、世界观、大纲、目标故事卷为 locked，相关角色至少 confirmed（可传 `?volume_id=`）

锁定资产不可通过普通编辑接口覆盖。

### 生成 API（Phase 3）

- `POST /api/projects/{project_id}/generation` — 触发 AI 生成（需通过准入检查）
- `GET /api/projects/{project_id}/generation/jobs` — 生成任务列表
- `GET /api/generation/jobs/{job_id}` — 任务详情
- `GET /api/projects/{project_id}/chapters?volume_id=` — 章节列表
- `GET /api/chapters/{chapter_id}` — 章节详情
- `PATCH /api/chapters/{chapter_id}` — 编辑章节草稿（锁定后不可编辑）

生成请求体：

```json
{
  "target_stage": "outline | volumes | chapters",
  "outline_id": "可选，故事卷生成时指定目标大纲",
  "volume_id": "章节生成时必填"
}
```

Phase 3 使用 `AI_PROVIDER=mock` 同步生成草稿资产（大纲 / 故事卷 / 章节），生成结果默认为 `draft` 状态，需走 Phase 2 确认锁定流程。

### 生成 API（Phase 4 扩展）

- 请求体新增 `batch_count`（1–10，仅章节生成有效）
- 响应改为 `{ jobs: GenerationJob[], total: number }`
- `GET /api/projects/{project_id}/export` — 成稿 JSON（默认仅已锁定章节）
- `GET /api/projects/{project_id}/export/download` — 下载成稿（`format`: `markdown` | `text` | `epub`）

LLM 配置（`apps/api/.env`）：

| 变量 | 说明 |
|------|------|
| `AI_PROVIDER` | `mock`（默认）或 `openai` |
| `AI_MODEL` | 模型名称，如 `gpt-4o-mini` |
| `OPENAI_API_KEY` | OpenAI 兼容 API Key |
| `OPENAI_BASE_URL` | 默认 `https://api.openai.com/v1` |
| `AI_BATCH_MAX_CHAPTERS` | 单次批量章节上限，默认 5 |

### 异步生成（Phase 5）

- 请求体 `async_mode: true` 时任务立即返回 `queued`，后台 worker 执行
- 前端通过 `GET /api/generation/jobs/{job_id}` 轮询状态
- 测试环境可设 `GENERATION_FORCE_SYNC=1` 强制同步执行

### 多模型路由（Phase 5）

| 档位 | 环境变量 |
|------|----------|
| 阶段专用 | `AI_MODEL_OUTLINE` / `AI_MODEL_VOLUME` / `AI_MODEL_CHAPTER` |
| fast | `AI_MODEL_PROFILE_FAST` |
| quality | `AI_MODEL_PROFILE_QUALITY` |

请求体 `model_profile`: `default` | `fast` | `quality`

### 发布 API（Phase 5）

- `POST /api/projects/{project_id}/publish` — 发布已锁定章节到本地存储
- `GET /api/projects/{project_id}/publications` — 发布记录列表
- `GET /api/publications/{id}/download` — 下载发布成稿

### 任务队列（Phase 6–8）

- `GENERATION_QUEUE_BACKEND`: `auto` | `thread` | `redis` | `celery`
- `auto` 优先级：`CELERY_BROKER_URL` → `REDIS_URL` → 线程
- Redis 消费：`python scripts/run_worker.py`
- Celery 消费：`python scripts/run_celery_worker.py`
- `POST /api/generation/jobs/{job_id}/cancel` — 取消 `queued` 任务（Celery 会 revoke task）

### 外部发布（Phase 6–8）

- 发布请求 `channel`: `local` | `webhook` | `platform`
- 发布请求 `format`: `markdown` | `text` | `epub`
- `POST /api/publications/{id}/retry-delivery` — 重试失败的 Webhook/平台投递
- 平台载荷预设 `PUBLISH_PLATFORM_PRESET`: `default`（摘要）| `minimal`（无正文）| `full`（完整 Markdown）
- 响应含 `delivery_status`、`external_ref`、`delivery_error`

### 素材库与文风（Phase 9–10）

**展示原则：** UI 与 Skill 均以 **作者** 为第一标识，作品名为次要信息。

**素材库（独立，不依赖创作项目）：**

- `POST /api/materials/references/upload` — multipart：`author`（必填）、`title`（可选）、`file`（txt/md/epub）
- `POST /api/materials/references/inspect-epub` — EPUB metadata 预填建议
- `GET /api/materials/references` — 全局参考列表
- `POST /api/materials/references/{id}/analyze` — 文风分析
- `GET /api/materials/style-analysis/jobs/{job_id}` — 分析任务状态

**技能库（设置页管理）：**

- `GET/PATCH /api/materials/style-profiles/{id}` — 文风画像编辑
- `POST .../confirm` · `POST .../lock` · `POST .../unlock` · `DELETE ...` — 生命周期
- `GET .../export/skill` — 下载 Skill zip

**项目绑定：**

- `POST /api/projects/{project_id}/materials/style-profiles/{id}/bind` — 绑定已锁定技能
- `GET /api/projects/{project_id}/materials/active-style` — 当前绑定（返回 `author`）

### 设置中心（Phase 10）

工作区设置持久化于 PostgreSQL `workspace_settings`（单例），PATCH 后即时更新运行时 AI 配置。

- `GET /api/settings` — 个人信息 + 模型配置（API Key 掩码）
- `PATCH /api/settings/personal` — `display_name`, `pen_name`, `bio`
- `PATCH /api/settings/models` — provider、模型、分阶段/档位映射、`default_model_profile`
- `POST /api/settings/models/test` — 连接测试
- `GET /api/settings/models/effective` — 阶段 × 档位 → 解析模型预览

`profile_json` 字段：`pov`, `sentence_rhythm`, `dialogue_ratio`, `pacing`, `emotional_tone`, `vocabulary`, `techniques`, `hooks`, `example_excerpts`

绑定且锁定的文风会注入章节生成 Prompt：`【文风约束】（模仿作者：{author}，参考《{title}》）`
