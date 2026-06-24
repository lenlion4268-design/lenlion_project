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
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
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

export async function fetchHealth(): Promise<{ status: string } | null> {
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

export { ApiError };
export type { ConfirmStatus, LockStatus, ReadinessResponse, ReviewTargetType };
