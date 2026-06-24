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
- 健康检查：`GET /api/health` → `{ "status": "ok" }`
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
