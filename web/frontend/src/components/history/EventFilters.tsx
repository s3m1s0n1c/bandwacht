import { Search, Download } from 'lucide-react'
import { events } from '../../api/client'
import { UI } from '../../utils/strings'

interface EventFiltersProps {
  label: string
  onLabelChange: (v: string) => void
  dateFrom: string
  onDateFromChange: (v: string) => void
  dateTo: string
  onDateToChange: (v: string) => void
}

export default function EventFilters({
  label, onLabelChange,
  dateFrom, onDateFromChange,
  dateTo, onDateToChange,
}: EventFiltersProps) {
  return (
    <div className="flex flex-wrap items-end gap-3">
      <div>
        <label className="label">Bezeichnung</label>
        <div className="relative">
          <Search className="w-3.5 h-3.5 text-sdr-muted absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            className="input pl-9 w-48"
            placeholder="Suchen..."
            value={label}
            onChange={e => onLabelChange(e.target.value)}
          />
        </div>
      </div>
      <div>
        <label className="label">Von</label>
        <input
          type="date"
          className="input"
          value={dateFrom}
          onChange={e => onDateFromChange(e.target.value)}
        />
      </div>
      <div>
        <label className="label">Bis</label>
        <input
          type="date"
          className="input"
          value={dateTo}
          onChange={e => onDateToChange(e.target.value)}
        />
      </div>
      <a
        href={events.exportCsv()}
        className="btn-ghost flex items-center gap-1.5"
        download
      >
        <Download className="w-3.5 h-3.5" />
        {UI.hist_export_csv}
      </a>
    </div>
  )
}
