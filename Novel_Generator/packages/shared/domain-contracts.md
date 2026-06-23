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

## API 约定

- API 前缀：`/api`
- 健康检查：`GET /api/health` → `{ "status": "ok" }`
- 前端通过 `NEXT_PUBLIC_API_BASE_URL` 访问后端（默认 `http://localhost:8000/api`）
