const BASE = '/api/v1'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(body.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

// --- Instances ---

export const instances = {
  list: () => request<import('../types').SdrInstance[]>('/instances'),
  get: (id: number) => request<import('../types').SdrInstance>(`/instances/${id}`),
  create: (data: { name: string; url: string; enabled?: boolean }) =>
    request<import('../types').SdrInstance>('/instances', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  update: (id: number, data: Partial<{ name: string; url: string; enabled: boolean }>) =>
    request<import('../types').SdrInstance>(`/instances/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  delete: (id: number) => request<{ ok: boolean }>(`/instances/${id}`, { method: 'DELETE' }),
  start: (id: number) => request<{ ok: boolean }>(`/instances/${id}/start`, { method: 'POST' }),
  stop: (id: number) => request<{ ok: boolean }>(`/instances/${id}/stop`, { method: 'POST' }),
  status: (id: number) => request<any>(`/instances/${id}/status`),
}

// --- Targets ---

export const targets = {
  list: (instanceId?: number) =>
    request<import('../types').WatchTarget[]>(
      `/targets${instanceId != null ? `?instance_id=${instanceId}` : ''}`
    ),
  create: (data: {
    instance_id: number
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
  create: (data: { backend: string; enabled?: boolean; config_json?: Record<string, unknown> }) =>
    request<import('../types').NotificationConfig>('/notifications', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  update: (id: number, data: Partial<{ enabled: boolean; config_json: Record<string, unknown> }>) =>
    request<import('../types').NotificationConfig>(`/notifications/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  delete: (id: number) => request<{ ok: boolean }>(`/notifications/${id}`, { method: 'DELETE' }),
  test: (id: number) => request<{ ok: boolean }>(`/notifications/${id}/test`, { method: 'POST' }),
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
