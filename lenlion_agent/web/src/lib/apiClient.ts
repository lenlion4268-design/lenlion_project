function apiBase(): string {
  return `${window.__HERMES_BASE_PATH__ || ''}/api`
}

export function getApiBase(): string {
  return apiBase()
}

export function buildAuthHeaders(): Record<string, string> {
  const headers: Record<string, string> = {
    Accept: 'application/json',
  }
  if (window.__HERMES_SESSION_TOKEN__) {
    headers['X-Hermes-Session-Token'] = window.__HERMES_SESSION_TOKEN__
  }
  return headers
}

async function parseError(res: Response): Promise<string> {
  const text = await res.text()
  try {
    const json = JSON.parse(text) as { detail?: string }
    return json.detail || text || res.statusText
  } catch {
    return text || res.statusText
  }
}

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${apiBase()}${path}`, { headers: buildAuthHeaders() })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json() as Promise<T>
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${apiBase()}${path}`, {
    method: 'POST',
    headers: { ...buildAuthHeaders(), 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json() as Promise<T>
}

export async function apiPut<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${apiBase()}${path}`, {
    method: 'PUT',
    headers: { ...buildAuthHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json() as Promise<T>
}

export async function apiDelete<T>(path: string): Promise<T> {
  const res = await fetch(`${apiBase()}${path}`, {
    method: 'DELETE',
    headers: buildAuthHeaders(),
  })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json() as Promise<T>
}
