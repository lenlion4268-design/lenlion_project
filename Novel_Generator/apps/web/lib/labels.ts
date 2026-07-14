import type { ConfirmStatus, LockStatus, ProjectMode, ProjectStage, ProjectStatus } from "@/lib/types";

export const MODE_LABELS: Record<ProjectMode, string> = {
  long: "长篇",
  short: "短篇",
};

export const STATUS_LABELS: Record<ProjectStatus, string> = {
  active: "进行中",
  archived: "已归档",
};

export const STAGE_LABELS: Record<ProjectStage, string> = {
  characters: "角色卡",
  theme: "主题题材",
  world: "世界观",
  outline: "大纲",
  volumes: "故事卷",
  chapters: "章节",
};

export const CONFIRM_STATUS_LABELS: Record<ConfirmStatus, string> = {
  draft: "草稿",
  pending_confirm: "待确认",
  confirmed: "已确认",
  locked: "已锁定",
  rejected: "已驳回",
  archived: "已归档",
};

export const GENRE_OPTIONS = [
  "玄幻",
  "仙侠",
  "都市",
  "历史",
  "科幻",
  "悬疑",
  "奇幻",
  "现实",
  "轻小说",
  "其他",
];

export const LOCK_STATUS_LABELS: Record<LockStatus, string> = {
  unlocked: "未锁定",
  locked: "已锁定",
};

export const REFERENCE_WORK_STATUS_LABELS: Record<string, string> = {
  uploaded: "已上传",
  ingested: "已采样",
  failed: "处理失败",
};

export const MATERIAL_SOURCE_LABELS: Record<string, string> = {
  reference_parse: "参考小说",
  own_completed: "已完成作品",
  manual: "手动录入",
  ai_suggested: "AI 建议",
};

export const STYLE_ANALYSIS_JOB_STATUS_LABELS: Record<string, string> = {
  queued: "排队中",
  running: "分析中",
  succeeded: "已完成",
  failed: "失败",
  cancelled: "已取消",
};

export function labelOrRaw(labels: Record<string, string>, value: string): string {
  return labels[value] ?? value;
}

export const REVIEW_ACTION_LABELS: Record<string, string> = {
  confirm: "确认",
  lock: "锁定",
  reject: "驳回",
  unlock: "解锁",
};

export function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}
