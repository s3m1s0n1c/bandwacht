import { useCallback, useEffect, useRef, useState } from 'react'
import { Activity, Radio, AlertTriangle } from 'lucide-react'
import { instances as instancesApi } from '../../api/client'
import { useWebSocket } from '../../hooks/useWebSocket'
import { UI } from '../../utils/strings'
import SpectrumDisplay from './SpectrumDisplay'
import EventFeed from './EventFeed'
import InstanceStatusCard from './InstanceStatusCard'
import type { SdrInstance } from '../../types'

interface LiveEvent {
  type: string
  instance_id: number
  timestamp: string
  freq_hz: number
  peak_db: number
  target_label: string
}

export default function Dashboard() {
  const [instances, setInstances] = useState<SdrInstance[]>([])
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [fftData, setFftData] = useState<number[] | null>(null)
  const [liveEvents, setLiveEvents] = useState<LiveEvent[]>([])
  const [runningIds, setRunningIds] = useState<Set<number>>(new Set())

  const refreshInstances = useCallback(async () => {
    const data = await instancesApi.list()
    setInstances(data)
    // Check which are running
    const running = new Set<number>()
    for (const inst of data) {
      try {
        const status = await instancesApi.status(inst.id)
        if (status.running) running.add(inst.id)
      } catch (_) { /* ignore */ }
    }
    setRunningIds(running)
    if (data.length > 0 && selectedId === null) {
      setSelectedId(data[0].id)
    }
  }, [selectedId])

  useEffect(() => { refreshInstances() }, [refreshInstances])

  // Poll instance status
  useEffect(() => {
    const interval = setInterval(refreshInstances, 5000)
    return () => clearInterval(interval)
  }, [refreshInstances])

  // FFT WebSocket
  useWebSocket({
    url: selectedId ? `/ws/spectrum/${selectedId}` : '/ws/spectrum/0',
    enabled: selectedId != null && runningIds.has(selectedId),
    onMessage: useCallback((data: number[]) => setFftData(data), []),
  })

  // Events WebSocket
  const eventsRef = useRef(liveEvents)
  eventsRef.current = liveEvents
  useWebSocket({
    url: '/ws/events',
    enabled: runningIds.size > 0,
    onMessage: useCallback((data: LiveEvent) => {
      setLiveEvents(prev => [data, ...prev].slice(0, 50))
    }, []),
  })

  const selected = instances.find(i => i.id === selectedId)

  return (
    <div className="space-y-6">
      {/* Status cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-sdr-cyan/10 flex items-center justify-center">
            <Radio className="w-5 h-5 text-sdr-cyan" />
          </div>
          <div>
            <p className="text-sm text-sdr-muted">{UI.dash_instances}</p>
            <p className="text-xl font-bold">{instances.length}</p>
          </div>
        </div>
        <div className="card flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-sdr-green/10 flex items-center justify-center">
            <Activity className="w-5 h-5 text-sdr-green" />
          </div>
          <div>
            <p className="text-sm text-sdr-muted">Aktive Monitore</p>
            <p className="text-xl font-bold">{runningIds.size}</p>
          </div>
        </div>
        <div className="card flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-sdr-amber/10 flex items-center justify-center">
            <AlertTriangle className="w-5 h-5 text-sdr-amber" />
          </div>
          <div>
            <p className="text-sm text-sdr-muted">{UI.dash_events}</p>
            <p className="text-xl font-bold">{liveEvents.length}</p>
          </div>
        </div>
      </div>

      {/* Instance cards */}
      {instances.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {instances.map(inst => (
            <InstanceStatusCard
              key={inst.id}
              instance={inst}
              isRunning={runningIds.has(inst.id)}
              onRefresh={refreshInstances}
              onSelect={setSelectedId}
              selected={selectedId === inst.id}
            />
          ))}
        </div>
      )}

      {/* Spectrum */}
      <div className="card">
        <h3 className="text-sm font-medium text-sdr-muted mb-3">
          {UI.dash_spectrum}
          {selected && <span className="text-sdr-cyan ml-2">— {selected.name}</span>}
        </h3>
        {selected && runningIds.has(selected.id) && selected.center_freq && selected.bandwidth ? (
          <SpectrumDisplay
            fftData={fftData}
            centerFreq={selected.center_freq}
            bandwidth={selected.bandwidth}
          />
        ) : (
          <div className="h-64 bg-sdr-bg rounded-lg flex items-center justify-center border border-sdr-border">
            <p className="text-sdr-muted text-sm">
              {instances.length === 0 ? UI.dash_no_instances : 'Monitor starten, um Spektrum anzuzeigen.'}
            </p>
          </div>
        )}
      </div>

      {/* Live events */}
      <div className="card">
        <h3 className="text-sm font-medium text-sdr-muted mb-3">{UI.dash_events}</h3>
        <EventFeed events={liveEvents} />
      </div>
    </div>
  )
}
