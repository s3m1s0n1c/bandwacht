const BASE = '/api/v1'

const TOKEN_KEY = 'bandwacht_token'

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY)
}

let onAuthError: (() => void) | null = null

export function setOnAuthError(cb: () => void): void {
  onAuthError = cb
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  const token = getToken()
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  const res = await fetch(`${BASE}${path}`, {
    headers: { ...headers, ...options?.headers },
    ...options,
  })
  if (res.status === 401) {
    clearToken()
    onAuthError?.()
    throw new Error('Nicht autorisiert')
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(body.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

// --- Auth ---

export const auth = {
  login: async (username: string, password: string): Promise<import('../types').TokenResponse> => {
    const body = new URLSearchParams({ username, password, grant_type: 'password' })
    const res = await fetch(`${BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body,
    })
    if (!res.ok) {
      const data = await res.json().catch(() => ({ detail: res.statusText }))
      throw new Error(data.detail || `HTTP ${res.status}`)
    }
    const data: import('../types').TokenResponse = await res.json()
    setToken(data.access_token)
    return data
  },
  logout: () => {
    clearToken()
  },
}

// --- Instances ---

export const instances = {
  list: () => request<import('../types').SdrInstance[]>('/instances'),
  get: (id: number) => request<import('../types').SdrInstance>(`/instances/${id}`),
  create: (data: { name: string; url: string; enabled?: boolean; desired_profile?: string | null; grid_locator?: string | null }) =>
    request<import('../types').SdrInstance>('/instances', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  update: (id: number, data: Partial<{ name: string; url: string; enabled: boolean; desired_profile: string | null; grid_locator: string | null }>) =>
    request<import('../types').SdrInstance>(`/instances/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  delete: (id: number) => request<{ ok: boolean }>(`/instances/${id}`, { method: 'DELETE' }),
  start: (id: number) => request<{ ok: boolean }>(`/instances/${id}/start`, { method: 'POST' }),
  stop: (id: number) => request<{ ok: boolean }>(`/instances/${id}/stop`, { method: 'POST' }),
  status: (id: number) => request<any>(`/instances/${id}/status`),
  profiles: (id: number) => request<import('../types').AvailableProfile[]>(`/instances/${id}/profiles`),
}

// --- Targets ---

export const targets = {
  list: (instanceId?: number) =>
    request<import('../types').WatchTarget[]>(
      `/targets${instanceId != null ? `?instance_id=${instanceId}` : ''}`
    ),
  create: (data: {
    instance_id: number | null
    freq_hz: number
    bandwidth_hz?: number
    label?: string
    threshold_db?: number
    enabled?: boolean
  }) =>
    request<import('../types').WatchTarget>('/targets', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  update: (id: number, data: Partial<import('../types').WatchTarget>) =>
    request<import('../types').WatchTarget>(`/targets/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  delete: (id: number) => request<{ ok: boolean }>(`/targets/${id}`, { method: 'DELETE' }),
}

// --- Events ---

export const events = {
  list: (params?: {
    page?: number
    page_size?: number
    instance_id?: number
    freq_min?: number
    freq_max?: number
    date_from?: string
    date_to?: string
    label?: string
  }) => {
    const searchParams = new URLSearchParams()
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v != null) searchParams.set(k, String(v))
      })
    }
    const qs = searchParams.toString()
    return request<import('../types').PaginatedResponse<import('../types').DetectionEvent>>(
      `/events${qs ? `?${qs}` : ''}`
    )
  },
  stats: () => request<import('../types').EventStats>('/events/stats'),
  exportCsv: () => `${BASE}/events/export`,
}

// --- Recordings ---

export const recordings = {
  list: () => request<string[]>('/recordings'),
  url: (filename: string) => `${BASE}/recordings/${encodeURIComponent(filename)}`,
  delete: (filename: string) =>
    request<{ ok: boolean }>(`/recordings/${encodeURIComponent(filename)}`, { method: 'DELETE' }),
}

// --- Notifications ---

export const notifications = {
  list: () => request<import('../types').NotificationConfig[]>('/notifications'),
  test: (backend: string) => request<{ ok: boolean }>(`/notifications/${backend}/test`, { method: 'POST' }),
}

// --- Settings ---

export const settings = {
  get: () => request<import('../types').GlobalSettings>('/settings'),
  update: (data: Partial<import('../types').GlobalSettings>) =>
    request<import('../types').GlobalSettings>('/settings', {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
}

// --- Health ---

export const health = () => request<{ status: string; version: string }>('/health')
