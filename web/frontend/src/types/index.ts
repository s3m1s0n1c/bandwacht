export interface SdrInstance {
  id: number
  name: string
  url: string
  enabled: boolean
  is_connected: boolean
  center_freq: number | null
  bandwidth: number | null
  fft_size: number | null
  created_at: string
  updated_at: string
}

export interface WatchTarget {
  id: number
  instance_id: number
  freq_hz: number
  bandwidth_hz: number
  label: string
  threshold_db: number
  enabled: boolean
  created_at: string
  updated_at: string
}

export interface DetectionEvent {
  id: number
  instance_id: number
  target_id: number | null
  timestamp: string
  freq_hz: number
  peak_db: number
  bandwidth_hz: number
  duration_s: number
  target_label: string
  recording_file: string | null
}

export interface NotificationConfig {
  id: number
  backend: string
  enabled: boolean
  config_json: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface GlobalSettings {
  threshold_db: number
  hysteresis_db: number
  hold_time_s: number
  cooldown_s: number
  record_enabled: boolean
  scan_full_band: boolean
}

export interface EventStats {
  total_events: number
  events_today: number
  events_this_week: number
  top_frequencies: Array<{ freq_hz: number; count: number; label: string }>
  hourly_distribution: Array<{ hour: number; count: number }>
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

export type Page = 'dashboard' | 'config' | 'history'
