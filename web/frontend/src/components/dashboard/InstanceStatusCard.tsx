import { Play, Square, Radio } from 'lucide-react'
import { instances as api } from '../../api/client'
import { formatFreqShort } from '../../utils/format'
import { UI } from '../../utils/strings'
import StatusBadge from '../shared/StatusBadge'
import type { SdrInstance } from '../../types'

interface InstanceStatusCardProps {
  instance: SdrInstance
  isRunning: boolean
  onRefresh: () => void
  onSelect: (id: number) => void
  selected: boolean
}

export default function InstanceStatusCard({ instance, isRunning, onRefresh, onSelect, selected }: InstanceStatusCardProps) {
  const handleStart = async (e: React.MouseEvent) => {
    e.stopPropagation()
    await api.start(instance.id)
    onRefresh()
  }

  const handleStop = async (e: React.MouseEvent) => {
    e.stopPropagation()
    await api.stop(instance.id)
    onRefresh()
  }

  return (
    <div
      onClick={() => onSelect(instance.id)}
      className={`card cursor-pointer transition-colors ${
        selected ? 'border-sdr-cyan' : 'hover:border-sdr-border/80'
      }`}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Radio className="w-4 h-4 text-sdr-cyan" />
          <span className="text-sm font-medium">{instance.name}</span>
        </div>
        <StatusBadge
          active={instance.is_connected}
          activeText={UI.dash_connected}
          inactiveText={UI.dash_disconnected}
        />
      </div>

      <p className="text-xs text-sdr-muted mb-2 truncate">{instance.url}</p>

      {instance.center_freq && instance.bandwidth && (
        <p className="text-xs text-sdr-muted mb-3">
          {formatFreqShort(instance.center_freq)} &middot; {formatFreqShort(instance.bandwidth)} BW
        </p>
      )}

      <div className="flex gap-2">
        {isRunning ? (
          <button onClick={handleStop} className="btn-danger flex items-center gap-1.5 text-xs py-1.5">
            <Square className="w-3 h-3" />
            {UI.dash_stop}
          </button>
        ) : (
          <button onClick={handleStart} className="btn-primary flex items-center gap-1.5 text-xs py-1.5">
            <Play className="w-3 h-3" />
            {UI.dash_start}
          </button>
        )}
      </div>
    </div>
  )
}
