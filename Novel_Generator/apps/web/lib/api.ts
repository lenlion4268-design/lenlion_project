import type {
  CharacterCard,
  CharacterProfile,
  ConfirmStatus,
  LockStatus,
  NovelProject,
  Outline,
  ProjectListResponse,
  ProjectMode,
  ProjectStatus,
  ReadinessResponse,
  ReadinessStage,
  ReviewAction,
  ReviewResponse,
  ReviewTargetType,
  ThemeProfile,
  Volume,
  Chapter,
  ExportFormat,
  GenerationJob,
  ModelProfile,
  Publication,
  PublishChannel,
  ReferenceWork,
  StyleAnalysisJob,
  StyleProfile,
  ActiveStyle,
  SettingsResponse,
  PersonalSettings,
  ModelSettings,
  ModelTestResponse,
  EffectiveModelsResponse,
  WorldBackground,
  WorldSetting,
} from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";

class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const isFormData = typeof FormData !== "undefined" && init?.body instanceof FormData;
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: isFormData
      ? { ...init?.headers }
      : {
          "Content-Type": "application/json",
          ...init?.headers,
        },
    cache: "no-store",
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = (await response.json()) as { detail?: string };
      detail = body.detail ?? detail;
    } catch {
      // ignore parse errors
    }
    throw new ApiError(response.status, detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export async function fetchHealth(): Promise<{
  status: string;
  queue_backend?: string;
  redis_connected?: boolean;
} | null> {
  try {
    return await request<{ status: string }>("/health");
  } catch {
    return null;
  }
}

export function listProjects(status?: ProjectStatus): Promise<ProjectListResponse> {
  const query = status ? `?status=${status}` : "";
  return request<ProjectListResponse>(`/projects${query}`);
}

export function createProject(data: {
  title: string;
  genre: string;
  mode: ProjectMode;
}): Promise<NovelProject> {
  return request<NovelProject>("/projects", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function getProject(projectId: string): Promise<NovelProject> {
  return request<NovelProject>(`/projects/${projectId}`);
}

export function updateProject(
  projectId: string,
  data: Partial<Pick<NovelProject, "title" | "genre" | "current_stage" | "status">>,
): Promise<NovelProject> {
  return request<NovelProject>(`/projects/${projectId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function listCharacterCards(projectId: string): Promise<{ items: CharacterCard[]; total: number }> {
  return request(`/projects/${projectId}/character-cards`);
}

export function createCharacterCard(
  projectId: string,
  data: { name: string; profile_json?: CharacterProfile },
): Promise<CharacterCard> {
  return request(`/projects/${projectId}/character-cards`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updateCharacterCard(
  cardId: string,
  data: { name?: string; profile_json?: CharacterProfile },
): Promise<CharacterCard> {
  return request(`/character-cards/${cardId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function getThemeProfile(projectId: string): Promise<ThemeProfile> {
  return request(`/projects/${projectId}/theme-profile`);
}

export function saveThemeProfile(
  projectId: string,
  data: Partial<Omit<ThemeProfile, "id" | "project_id" | "confirm_status" | "lock_status" | "created_at" | "updated_at">>,
): Promise<ThemeProfile> {
  return request(`/projects/${projectId}/theme-profile`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export function getWorldSetting(projectId: string): Promise<WorldSetting> {
  return request(`/projects/${projectId}/world-setting`);
}

export function saveWorldSetting(
  projectId: string,
  data: { background_json: WorldBackground },
): Promise<WorldSetting> {
  return request(`/projects/${projectId}/world-setting`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export function listOutlines(projectId: string): Promise<{ items: Outline[]; total: number }> {
  return request(`/projects/${projectId}/outlines`);
}

export function createOutline(
  projectId: string,
  data: { title?: string; summary?: string; ending_direction?: string },
): Promise<Outline> {
  return request(`/projects/${projectId}/outlines`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function listVolumes(projectId: string): Promise<{ items: Volume[]; total: number }> {
  return request(`/projects/${projectId}/volumes`);
}

export function createVolume(
  projectId: string,
  data: { title?: string; volume_no?: number; stage_goal?: string; outline_id?: string | null },
): Promise<Volume> {
  return request(`/projects/${projectId}/volumes`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function submitReview(
  action: ReviewAction,
  data: { target_type: ReviewTargetType; target_id: string; comment?: string },
): Promise<ReviewResponse> {
  return request(`/review/${action}`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function getReadiness(
  projectId: string,
  targetStage: ReadinessStage,
  params?: { outline_id?: string; volume_id?: string },
): Promise<ReadinessResponse> {
  const query = new URLSearchParams();
  if (params?.outline_id) query.set("outline_id", params.outline_id);
  if (params?.volume_id) query.set("volume_id", params.volume_id);
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return request(`/projects/${projectId}/readiness/${targetStage}${suffix}`);
}

export function createGenerationJob(
  projectId: string,
  data: {
    target_stage: ReadinessStage;
    outline_id?: string;
    volume_id?: string;
    batch_count?: number;
    model_profile?: ModelProfile;
    async_mode?: boolean;
  },
): Promise<{ jobs: GenerationJob[]; total: number }> {
  return request(`/projects/${projectId}/generation`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function getGenerationJob(jobId: string): Promise<GenerationJob> {
  return request(`/generation/jobs/${jobId}`);
}

export function listGenerationJobs(projectId: string): Promise<{ items: GenerationJob[]; total: number }> {
  return request(`/projects/${projectId}/generation/jobs`);
}

export function listChapters(
  projectId: string,
  volumeId?: string,
): Promise<{ items: Chapter[]; total: number }> {
  const query = volumeId ? `?volume_id=${encodeURIComponent(volumeId)}` : "";
  return request(`/projects/${projectId}/chapters${query}`);
}

export function getChapter(chapterId: string): Promise<Chapter> {
  return request(`/chapters/${chapterId}`);
}

export function updateChapter(
  chapterId: string,
  data: { title?: string; content?: string },
): Promise<Chapter> {
  return request(`/chapters/${chapterId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function exportManuscript(
  projectId: string,
  params?: { volume_id?: string; include_drafts?: boolean; format?: ExportFormat },
): Promise<{ project_id: string; volume_id: string | null; format: string; chapter_count: number; content: string; file_size?: number | null }> {
  const query = new URLSearchParams();
  if (params?.volume_id) query.set("volume_id", params.volume_id);
  if (params?.include_drafts) query.set("include_drafts", "true");
  if (params?.format) query.set("format", params.format);
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return request(`/projects/${projectId}/export${suffix}`);
}

export function downloadManuscript(
  projectId: string,
  params?: { volume_id?: string; include_drafts?: boolean; format?: ExportFormat },
): string {
  const query = new URLSearchParams();
  if (params?.volume_id) query.set("volume_id", params.volume_id);
  if (params?.include_drafts) query.set("include_drafts", "true");
  if (params?.format) query.set("format", params.format);
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return `${API_BASE_URL}/projects/${projectId}/export/download${suffix}`;
}

export function publishManuscript(
  projectId: string,
  data: {
    volume_id?: string;
    title?: string;
    format?: ExportFormat;
    channel?: PublishChannel;
  },
): Promise<Publication> {
  return request(`/projects/${projectId}/publish`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function listPublications(
  projectId: string,
): Promise<{ items: Publication[]; total: number }> {
  return request(`/projects/${projectId}/publications`);
}

export function downloadPublication(publicationId: string): string {
  return `${API_BASE_URL}/publications/${publicationId}/download`;
}

export function retryPublicationDelivery(publicationId: string): Promise<Publication> {
  return request(`/publications/${publicationId}/retry-delivery`, {
    method: "POST",
  });
}

export function cancelGenerationJob(jobId: string): Promise<GenerationJob> {
  return request(`/generation/jobs/${jobId}/cancel`, {
    method: "POST",
  });
}

export function uploadReference(data: {
  author: string;
  title?: string;
  file: File;
}): Promise<ReferenceWork> {
  const form = new FormData();
  form.append("author", data.author);
  if (data.title) form.append("title", data.title);
  form.append("file", data.file);
  return request("/materials/references/upload", {
    method: "POST",
    body: form,
    headers: {},
  });
}

export function listReferences(): Promise<{ items: ReferenceWork[]; total: number }> {
  return request("/materials/references");
}

export function analyzeReference(referenceId: string): Promise<StyleAnalysisJob> {
  return request(`/materials/references/${referenceId}/analyze`, {
    method: "POST",
  });
}

export function listStyleProfiles(): Promise<{ items: StyleProfile[]; total: number }> {
  return request("/materials/style-profiles");
}

export function lockStyleProfile(profileId: string): Promise<StyleProfile> {
  return request(`/materials/style-profiles/${profileId}/lock`, {
    method: "POST",
  });
}

export function bindStyleProfile(projectId: string, profileId: string): Promise<ActiveStyle> {
  return request(`/projects/${projectId}/materials/style-profiles/${profileId}/bind`, {
    method: "POST",
  });
}

export function getActiveStyle(projectId: string): Promise<ActiveStyle> {
  return request(`/projects/${projectId}/materials/active-style`);
}

export function downloadStyleSkill(profileId: string): string {
  return `${API_BASE_URL}/materials/style-profiles/${profileId}/export/skill`;
}

export function getSettings(): Promise<SettingsResponse> {
  return request("/settings");
}

export function patchPersonalSettings(data: Partial<PersonalSettings>): Promise<SettingsResponse> {
  return request("/settings/personal", {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function patchModelSettings(
  data: Partial<ModelSettings> & { openai_api_key?: string | null },
): Promise<SettingsResponse> {
  return request("/settings/models", {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function testModelConnection(): Promise<ModelTestResponse> {
  return request("/settings/models/test", { method: "POST" });
}

export function getEffectiveModels(): Promise<EffectiveModelsResponse> {
  return request("/settings/models/effective");
}

export function updateStyleProfile(
  profileId: string,
  data: Partial<Pick<StyleProfile, "name" | "voice_summary" | "skill_markdown">>,
): Promise<StyleProfile> {
  return request(`/materials/style-profiles/${profileId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function confirmStyleProfile(profileId: string): Promise<StyleProfile> {
  return request(`/materials/style-profiles/${profileId}/confirm`, { method: "POST" });
}

export function unlockStyleProfile(profileId: string): Promise<StyleProfile> {
  return request(`/materials/style-profiles/${profileId}/unlock`, { method: "POST" });
}

export function deleteStyleProfile(profileId: string): Promise<void> {
  return request(`/materials/style-profiles/${profileId}`, { method: "DELETE" });
}

export { ApiError };
export type { ConfirmStatus, LockStatus, ReadinessResponse, ReviewTargetType };
