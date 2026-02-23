import { useCallback, useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { events as api } from '../../api/client'
import { formatFreqShort } from '../../utils/format'
import { UI } from '../../utils/strings'
import type { EventStats } from '../../types'

export default function StatsPanel() {
  const [stats, setStats] = useState<EventStats | null>(null)

  const load = useCallback(async () => {
    try {
      const data = await api.stats()
      setStats(data)
    } catch { /* ignore */ }
  }, [])

  useEffect(() => { load() }, [load])

  if (!stats) return null

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div className="card text-center">
        <p className="text-sm text-sdr-muted">{UI.hist_total}</p>
        <p className="text-2xl font-bold text-sdr-cyan">{stats.total_events}</p>
      </div>
      <div className="card text-center">
        <p className="text-sm text-sdr-muted">{UI.hist_today}</p>
        <p className="text-2xl font-bold text-sdr-green">{stats.events_today}</p>
      </div>
      <div className="card text-center">
        <p className="text-sm text-sdr-muted">{UI.hist_week}</p>
        <p className="text-2xl font-bold text-sdr-amber">{stats.events_this_week}</p>
      </div>

      {stats.top_frequencies.length > 0 && (
        <div className="card md:col-span-3">
          <h4 className="text-sm font-medium text-sdr-muted mb-3">{UI.hist_top_freq}</h4>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={stats.top_frequencies}>
              <XAxis
                dataKey="freq_hz"
                tickFormatter={(v: number) => formatFreqShort(v)}
                tick={{ fill: '#9ca3af', fontSize: 10 }}
                axisLine={{ stroke: '#1f2937' }}
              />
              <YAxis
                tick={{ fill: '#9ca3af', fontSize: 10 }}
                axisLine={{ stroke: '#1f2937' }}
              />
              <Tooltip
                contentStyle={{ background: '#111827', border: '1px solid #1f2937', borderRadius: 8 }}
                labelFormatter={(v: number) => formatFreqShort(v)}
              />
              <Bar dataKey="count" fill="#06b6d4" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}
