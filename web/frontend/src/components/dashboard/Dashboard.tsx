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
  instance_name?: string
  instance_grid?: string
}

export default function Dashboard() {
  const [instances, setInstances] = useState<SdrInstance[]>([])
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [fftData, setFftData] = useState<number[] | null>(null)
  const [liveEvents, setLiveEvents] = useState<LiveEvent[]>([])
  const [runningIds, setRunningIds] = useState<number[]>([])
  const selectedIdRef = useRef(selectedId)
  selectedIdRef.current = selectedId

  const refreshInstances = useCallback(async () => {
    const data = await instancesApi.list()
    setInstances(data)
    const running: number[] = []
    for (const inst of data) {
      try {
        const status = await instancesApi.status(inst.id)
        if (status.running) running.push(inst.id)
      } catch (_) { /* ignore */ }
    }
    setRunningIds(running)
    if (data.length > 0 && selectedIdRef.current === null) {
      setSelectedId(data[0].id)
    }
  }, [])

  useEffect(() => { refreshInstances() }, [refreshInstances])

  // Poll instance status every 3s
  useEffect(() => {
    const interval = setInterval(refreshInstances, 3000)
    return () => clearInterval(interval)
  }, [refreshInstances])

  const isSelectedRunning = selectedId != null && runningIds.includes(selectedId)

  // FFT WebSocket
  const fftUrl = selectedId ? `/ws/spectrum/${selectedId}` : '/ws/spectrum/0'
  useWebSocket({
    url: fftUrl,
    enabled: isSelectedRunning,
    onMessage: useCallback((data: number[]) => setFftData(data), []),
  })

  // Events WebSocket
  useWebSocket({
    url: '/ws/events',
    enabled: runningIds.length > 0,
    onMessage: useCallback((data: LiveEvent) => {
      setLiveEvents(prev => [data, ...prev].slice(0, 50))
    }, []),
  })

  const selected = instances.find(i => i.id === selectedId)

  const handleStartAndSelect = useCallback(async (id: number) => {
    setSelectedId(id)
    setFftData(null)
    await instancesApi.start(id)
    // Poll rapidly after start to pick up connection info
    for (let i = 0; i < 5; i++) {
      await new Promise(r => setTimeout(r, 1000))
      await refreshInstances()
    }
  }, [refreshInstances])

  const handleStop = useCallback(async (id: number) => {
    await instancesApi.stop(id)
    setFftData(null)
    await refreshInstances()
  }, [refreshInstances])

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
            <p className="text-xl font-bold">{runningIds.length}</p>
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
              isRunning={runningIds.includes(inst.id)}
              onStart={handleStartAndSelect}
              onStop={handleStop}
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
        {isSelectedRunning ? (
          <SpectrumDisplay
            fftData={fftData}
            centerFreq={selected?.center_freq ?? 0}
            bandwidth={selected?.bandwidth ?? 0}
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
