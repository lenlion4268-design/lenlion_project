export type ProjectMode = "long" | "short";
export type ProjectStatus = "active" | "archived";
export type ProjectStage =
  | "characters"
  | "theme"
  | "world"
  | "outline"
  | "volumes"
  | "chapters";
export type ConfirmStatus =
  | "draft"
  | "pending_confirm"
  | "confirmed"
  | "locked"
  | "rejected"
  | "archived";

export type LockStatus = "unlocked" | "locked";

export type ReviewTargetType =
  | "character_card"
  | "theme_profile"
  | "world_setting"
  | "outline"
  | "volume"
  | "chapter";

export type ReviewAction = "confirm" | "lock" | "reject" | "unlock";

export type ReadinessStage = "outline" | "volumes" | "chapters";

export type GenerationJobStatus =
  | "queued"
  | "running"
  | "succeeded"
  | "failed"
  | "cancelled";

export type ModelProfile = "default" | "fast" | "quality";
export type ExecutionMode = "sync" | "async";

export type PublicationStatus = "draft" | "published" | "archived";
export type PublishChannel = "local" | "webhook" | "platform";
export type ExportFormat = "markdown" | "text" | "epub";
export type DeliveryStatus = "pending" | "succeeded" | "failed" | "skipped";

export interface ReadinessMissingItem {
  target_type: ReviewTargetType;
  target_id: string | null;
  label: string;
  reason: string;
}

export interface ReadinessResponse {
  project_id: string;
  target_stage: ReadinessStage;
  ready: boolean;
  missing_items: ReadinessMissingItem[];
  blocked_reasons: string[];
}

export interface ReviewResponse {
  target_type: ReviewTargetType;
  target_id: string;
  confirm_status: ConfirmStatus;
  lock_status: LockStatus;
  action: ReviewAction;
  review_record_id: string;
}

export interface NovelProject {
  id: string;
  title: string;
  genre: string;
  mode: ProjectMode;
  status: ProjectStatus;
  current_stage: ProjectStage;
  active_style_profile_id?: string | null;
  owner_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProjectListResponse {
  items: NovelProject[];
  total: number;
}

export interface CharacterProfile {
  personality?: string;
  abilities?: string;
  goals?: string;
  weaknesses?: string;
  experiences?: string;
  identity?: string;
  faction?: string;
  organization?: string;
}

export interface CharacterCard {
  id: string;
  project_id: string;
  name: string;
  card_type: "person" | "organization" | "force";
  profile_json: CharacterProfile;
  tags: string[];
  source_type: string;
  confirm_status: ConfirmStatus;
  lock_status: LockStatus;
  created_at: string;
  updated_at: string;
}

export interface ThemeProfile {
  id: string;
  project_id: string;
  genre: string;
  theme: string;
  target_readers: string;
  narrative_style: string;
  emotional_tone: string;
  pleasure_points: string;
  forbidden_content: string;
  confirm_status: ConfirmStatus;
  lock_status: LockStatus;
  created_at: string;
  updated_at: string;
}

export interface WorldBackground {
  era?: string;
  geography?: string;
  institutions?: string;
  power_system?: string;
  historical_events?: string;
  society?: string;
  technology_level?: string;
  culture?: string;
  conflicts?: string;
}

export interface WorldSetting {
  id: string;
  project_id: string;
  background_json: WorldBackground;
  confirm_status: ConfirmStatus;
  lock_status: LockStatus;
  created_at: string;
  updated_at: string;
}

export interface Outline {
  id: string;
  project_id: string;
  title: string;
  summary: string;
  plot_nodes_json: unknown[];
  character_arcs_json: unknown[];
  ending_direction: string;
  confirm_status: ConfirmStatus;
  lock_status: LockStatus;
  created_at: string;
  updated_at: string;
}

export interface Volume {
  id: string;
  project_id: string;
  outline_id: string | null;
  volume_no: number;
  title: string;
  stage_goal: string;
  main_conflict: string;
  key_events_json: unknown[];
  involved_characters: string[];
  emotional_rhythm: string;
  previous_relation: string;
  next_relation: string;
  confirm_status: ConfirmStatus;
  lock_status: LockStatus;
  created_at: string;
  updated_at: string;
}

export interface GenerationJob {
  id: string;
  project_id: string;
  target_stage: ReadinessStage;
  outline_id: string | null;
  volume_id: string | null;
  status: GenerationJobStatus;
  provider: string;
  model_profile: ModelProfile;
  model_name: string | null;
  execution_mode: ExecutionMode;
  result_type: ReviewTargetType | null;
  result_id: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

export interface Publication {
  id: string;
  project_id: string;
  volume_id: string | null;
  title: string;
  format: string;
  status: PublicationStatus;
  storage_path: string;
  chapter_count: number;
  word_count: number;
  channel: PublishChannel;
  delivery_status: DeliveryStatus;
  delivery_error: string | null;
  external_ref: string | null;
  created_at: string;
  published_at: string | null;
}

export interface Chapter {
  id: string;
  project_id: string;
  volume_id: string;
  generation_job_id: string | null;
  chapter_no: number;
  title: string;
  content: string;
  word_count: number;
  source_type: string;
  confirm_status: ConfirmStatus;
  lock_status: LockStatus;
  created_at: string;
  updated_at: string;
}

export interface ReferenceWork {
  id: string;
  project_id: string | null;
  author: string;
  title: string;
  format: string;
  word_count: number;
  source_type: string;
  status: string;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface StyleProfile {
  id: string;
  project_id: string | null;
  reference_work_id: string;
  author: string;
  reference_title: string;
  name: string;
  voice_summary: string;
  profile_json: Record<string, unknown>;
  skill_markdown: string;
  confirm_status: ConfirmStatus;
  lock_status: LockStatus;
  created_at: string;
  updated_at: string;
}

export interface StyleAnalysisJob {
  id: string;
  project_id: string | null;
  reference_work_id: string;
  style_profile_id: string | null;
  status: string;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

export interface ActiveStyle {
  active_style_profile_id: string | null;
  author: string | null;
  name: string | null;
}

export interface PersonalSettings {
  display_name: string | null;
  pen_name: string | null;
  bio: string | null;
}

export interface ModelSettings {
  ai_provider: string;
  ai_model: string;
  openai_base_url: string;
  openai_api_key_masked: string | null;
  ai_model_outline: string | null;
  ai_model_volume: string | null;
  ai_model_chapter: string | null;
  ai_model_profile_fast: string | null;
  ai_model_profile_quality: string | null;
  ai_request_timeout_seconds: number;
  ai_batch_max_chapters: number;
  default_model_profile: ModelProfile;
}

export interface SettingsResponse {
  personal: PersonalSettings;
  models: ModelSettings;
}

export interface ModelTestResponse {
  ok: boolean;
  message: string;
  provider: string;
}

export interface EffectiveModelRow {
  target_stage: string;
  model_profile: string;
  model_name: string;
}

export interface EffectiveModelsResponse {
  provider: string;
  rows: EffectiveModelRow[];
}
