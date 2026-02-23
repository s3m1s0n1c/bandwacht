import { useState } from 'react'
import { Pencil, Trash2, Plus } from 'lucide-react'
import { targets as api } from '../../api/client'
import { UI } from '../../utils/strings'
import { formatFreqMHz, formatDb } from '../../utils/format'
import StatusBadge from '../shared/StatusBadge'
import ConfirmDialog from '../shared/ConfirmDialog'
import TargetForm from './TargetForm'
import type { SdrInstance, WatchTarget } from '../../types'

interface TargetListProps {
  targets: WatchTarget[]
  instances: SdrInstance[]
  onRefresh: () => void
}

export default function TargetList({ targets, instances, onRefresh }: TargetListProps) {
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState<WatchTarget | null>(null)
  const [deleteId, setDeleteId] = useState<number | null>(null)

  const handleDelete = async () => {
    if (deleteId == null) return
    await api.delete(deleteId)
    setDeleteId(null)
    onRefresh()
  }

  const getInstanceName = (id: number) =>
    instances.find(i => i.id === id)?.name ?? `#${id}`

  return (
    <>
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-medium">{UI.cfg_targets}</h4>
        <button
          onClick={() => { setEditing(null); setShowForm(true) }}
          className="btn-primary flex items-center gap-1.5"
          disabled={instances.length === 0}
        >
          <Plus className="w-3.5 h-3.5" />
          {UI.cfg_add_target}
        </button>
      </div>

      {targets.length === 0 ? (
        <p className="text-sdr-muted text-sm py-4 text-center">
          {instances.length === 0 ? 'Zuerst eine SDR-Instanz anlegen.' : 'Keine Überwachungsziele konfiguriert.'}
        </p>
      ) : (
        <div className="space-y-2">
          {targets.map(t => (
            <div key={t.id} className="flex items-center justify-between p-3 bg-sdr-bg rounded-lg border border-sdr-border">
              <div className="flex items-center gap-3 min-w-0">
                <StatusBadge active={t.enabled} />
                <div className="min-w-0">
                  <p className="text-sm font-medium truncate">
                    {t.label || formatFreqMHz(t.freq_hz)}
                  </p>
                  <p className="text-xs text-sdr-muted">
                    {formatFreqMHz(t.freq_hz)} &middot; {(t.bandwidth_hz / 1000).toFixed(1)} kHz &middot; {formatDb(t.threshold_db)} &middot; {getInstanceName(t.instance_id)}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-1 shrink-0">
                <button
                  onClick={() => { setEditing(t); setShowForm(true) }}
                  className="p-1.5 text-sdr-muted hover:text-sdr-text transition-colors"
                >
                  <Pencil className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={() => setDeleteId(t.id)}
                  className="p-1.5 text-sdr-muted hover:text-sdr-red transition-colors"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {showForm && (
        <TargetForm
          target={editing}
          instances={instances}
          onClose={() => setShowForm(false)}
          onSaved={() => { setShowForm(false); onRefresh() }}
        />
      )}

      <ConfirmDialog
        open={deleteId != null}
        message={UI.confirm_delete}
        onConfirm={handleDelete}
        onCancel={() => setDeleteId(null)}
      />
    </>
  )
}
