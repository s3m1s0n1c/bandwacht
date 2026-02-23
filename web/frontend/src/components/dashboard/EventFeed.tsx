import { AlertTriangle } from 'lucide-react'
import { formatFreqMHz, formatDb, formatTime } from '../../utils/format'
import { UI } from '../../utils/strings'

interface LiveEvent {
  type: string
  instance_id: number
  timestamp: string
  freq_hz: number
  peak_db: number
  target_label: string
}

interface EventFeedProps {
  events: LiveEvent[]
}

export default function EventFeed({ events }: EventFeedProps) {
  if (events.length === 0) {
    return (
      <div className="text-sdr-muted text-sm py-8 text-center">
        {UI.hist_no_events}
      </div>
    )
  }

  return (
    <div className="space-y-1.5 max-h-64 overflow-auto">
      {events.map((ev, i) => (
        <div key={i} className="flex items-center gap-3 p-2 bg-sdr-bg rounded-lg border border-sdr-border/50 animate-pulse-once">
          <AlertTriangle className="w-3.5 h-3.5 text-sdr-red shrink-0" />
          <div className="flex-1 min-w-0">
            <span className="text-sm font-medium text-sdr-red">
              {ev.target_label || formatFreqMHz(ev.freq_hz)}
            </span>
            <span className="text-xs text-sdr-muted ml-2">
              {formatFreqMHz(ev.freq_hz)} &middot; {formatDb(ev.peak_db)}
            </span>
          </div>
          <span className="text-xs text-sdr-muted shrink-0">
            {formatTime(ev.timestamp)}
          </span>
        </div>
      ))}
    </div>
  )
}
