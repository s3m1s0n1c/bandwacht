import { Play } from 'lucide-react'
import { formatFreqMHz, formatDb, formatSValue, formatDuration, formatTimestamp } from '../../utils/format'
import { recordings } from '../../api/client'
import { UI } from '../../utils/strings'
import type { DetectionEvent } from '../../types'

interface EventTableProps {
  events: DetectionEvent[]
  onPlayRecording?: (url: string) => void
}

export default function EventTable({ events, onPlayRecording }: EventTableProps) {
  if (events.length === 0) {
    return <p className="text-sdr-muted text-sm py-8 text-center">{UI.hist_no_events}</p>
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-sdr-muted border-b border-sdr-border">
            <th className="pb-2 pr-4 font-medium">Zeitpunkt</th>
            <th className="pb-2 pr-4 font-medium">Frequenz</th>
            <th className="pb-2 pr-4 font-medium">Peak</th>
            <th className="pb-2 pr-4 font-medium">Dauer</th>
            <th className="pb-2 pr-4 font-medium">Bezeichnung</th>
            <th className="pb-2 font-medium w-10"></th>
          </tr>
        </thead>
        <tbody>
          {events.map(ev => (
            <tr key={ev.id} className="border-b border-sdr-border/30 hover:bg-sdr-border/10">
              <td className="py-2 pr-4 text-xs text-sdr-muted whitespace-nowrap">
                {formatTimestamp(ev.timestamp)}
              </td>
              <td className="py-2 pr-4 font-mono text-sdr-cyan whitespace-nowrap">
                {formatFreqMHz(ev.freq_hz)}
              </td>
              <td className="py-2 pr-4 font-mono whitespace-nowrap">
                <span className={ev.peak_db > -50 ? 'text-sdr-red' : 'text-sdr-amber'}>
                  {formatDb(ev.peak_db)} ({formatSValue(ev.peak_db)})
                </span>
              </td>
              <td className="py-2 pr-4 text-sdr-muted whitespace-nowrap">
                {formatDuration(ev.duration_s)}
              </td>
              <td className="py-2 pr-4 truncate max-w-[200px]">
                {ev.target_label || '—'}
              </td>
              <td className="py-2">
                {ev.recording_file && onPlayRecording && (
                  <button
                    onClick={() => onPlayRecording(recordings.url(ev.recording_file!))}
                    className="p-1 text-sdr-muted hover:text-sdr-green transition-colors"
                    title="Abspielen"
                  >
                    <Play className="w-3.5 h-3.5" />
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
