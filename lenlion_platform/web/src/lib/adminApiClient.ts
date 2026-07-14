import { adminToken, clearAdminSession } from '@/features/auth/authStore'

const API_BASE = ''

async function parseError(res: Response): Promise<string> {
  const text = await res.text()
  try {
    const json = JSON.parse(text) as { detail?: string }
    return json.detail || text || res.statusText
  } catch {
    return text || res.statusText
  }
}

function headers(): Record<string, string> {
  const token = adminToken.get()
  const h: Record<string, string> = { Accept: 'application/json' }
  if (token) h.Authorization = `Bearer ${token}`
  return h
}

export async function adminGet<T>(path: string, params?: Record<string, string>): Promise<T> {
  const qs = params ? `?${new URLSearchParams(params)}` : ''
  const res = await fetch(`${API_BASE}${path}${qs}`, { headers: headers() })
  if (res.status === 401 || res.status === 403) {
    clearAdminSession()
    throw new Error('unauthorized')
  }
  if (!res.ok) throw new Error(await parseError(res))
  return res.json() as Promise<T>
}

export async function adminPost<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: headers(),
  })
  if (res.status === 401 || res.status === 403) {
    clearAdminSession()
    throw new Error('unauthorized')
  }
  if (!res.ok) throw new Error(await parseError(res))
  return res.json() as Promise<T>
}

export function getApiBase(): string {
  return API_BASE
}

export function buildAuthHeaders(): Record<string, string> {
  return headers()
}
