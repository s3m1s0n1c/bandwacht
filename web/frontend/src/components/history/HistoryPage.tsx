import { useState } from 'react'
import { BookOpen, BarChart3, ChevronLeft, ChevronRight } from 'lucide-react'
import { useEvents } from '../../hooks/useEvents'
import { UI } from '../../utils/strings'
import EventTable from './EventTable'
import EventFilters from './EventFilters'
import AudioPlayer from './AudioPlayer'
import StatsPanel from './StatsPanel'

export default function HistoryPage() {
  const [page, setPage] = useState(1)
  const [label, setLabel] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [showStats, setShowStats] = useState(false)
  const [audioUrl, setAudioUrl] = useState<string | null>(null)

  const { items, total, pages, loading } = useEvents({
    page,
    page_size: 50,
    label: label || undefined,
    date_from: dateFrom || undefined,
    date_to: dateTo || undefined,
  })

  return (
    <div className="space-y-6">
      {/* Stats toggle */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-sdr-cyan" />
          <h3 className="text-sm font-medium">{UI.hist_title}</h3>
          <span className="text-xs text-sdr-muted">({total} Einträge)</span>
        </div>
        <button
          onClick={() => setShowStats(!showStats)}
          className="btn-ghost flex items-center gap-1.5"
        >
          <BarChart3 className="w-3.5 h-3.5" />
          {UI.hist_stats}
        </button>
      </div>

      {showStats && <StatsPanel />}

      {/* Filters */}
      <div className="card">
        <EventFilters
          label={label}
          onLabelChange={v => { setLabel(v); setPage(1) }}
          dateFrom={dateFrom}
          onDateFromChange={v => { setDateFrom(v); setPage(1) }}
          dateTo={dateTo}
          onDateToChange={v => { setDateTo(v); setPage(1) }}
        />
      </div>

      {/* Table */}
      <div className="card">
        {loading ? (
          <p className="text-sdr-muted text-sm py-8 text-center">{UI.loading}</p>
        ) : (
          <EventTable events={items} onPlayRecording={setAudioUrl} />
        )}

        {/* Pagination */}
        {pages > 1 && (
          <div className="flex items-center justify-between mt-4 pt-4 border-t border-sdr-border">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="btn-ghost flex items-center gap-1"
            >
              <ChevronLeft className="w-4 h-4" />
              Zurück
            </button>
            <span className="text-sm text-sdr-muted">
              Seite {page} von {pages}
            </span>
            <button
              onClick={() => setPage(p => Math.min(pages, p + 1))}
              disabled={page >= pages}
              className="btn-ghost flex items-center gap-1"
            >
              Weiter
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>

      {/* Audio player */}
      <AudioPlayer url={audioUrl} onClose={() => setAudioUrl(null)} />
    </div>
  )
}
