import { useState } from 'react'
import { Pencil, Trash2, Plus } from 'lucide-react'
import { instances as api } from '../../api/client'
import { UI } from '../../utils/strings'
import StatusBadge from '../shared/StatusBadge'
import ConfirmDialog from '../shared/ConfirmDialog'
import InstanceForm from './InstanceForm'
import type { SdrInstance } from '../../types'

interface InstanceListProps {
  instances: SdrInstance[]
  onRefresh: () => void
}

export default function InstanceList({ instances, onRefresh }: InstanceListProps) {
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState<SdrInstance | null>(null)
  const [deleteId, setDeleteId] = useState<number | null>(null)

  const handleDelete = async () => {
    if (deleteId == null) return
    await api.delete(deleteId)
    setDeleteId(null)
    onRefresh()
  }

  return (
    <>
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-medium">{UI.cfg_instances}</h4>
        <button onClick={() => { setEditing(null); setShowForm(true) }} className="btn-primary flex items-center gap-1.5">
          <Plus className="w-3.5 h-3.5" />
          {UI.cfg_add_instance}
        </button>
      </div>

      {instances.length === 0 ? (
        <p className="text-sdr-muted text-sm py-4 text-center">{UI.dash_no_instances}</p>
      ) : (
        <div className="space-y-2">
          {instances.map(inst => (
            <div key={inst.id} className="flex items-center justify-between p-3 bg-sdr-bg rounded-lg border border-sdr-border">
              <div className="flex items-center gap-3 min-w-0">
                <StatusBadge active={inst.enabled} activeText={UI.cfg_enabled} inactiveText="Deaktiviert" />
                <div className="min-w-0">
                  <p className="text-sm font-medium truncate">{inst.name}</p>
                  <p className="text-xs text-sdr-muted truncate">{inst.url}</p>
                </div>
              </div>
              <div className="flex items-center gap-1 shrink-0">
                <button
                  onClick={() => { setEditing(inst); setShowForm(true) }}
                  className="p-1.5 text-sdr-muted hover:text-sdr-text transition-colors"
                  title={UI.cfg_edit}
                >
                  <Pencil className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={() => setDeleteId(inst.id)}
                  className="p-1.5 text-sdr-muted hover:text-sdr-red transition-colors"
                  title={UI.cfg_delete}
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {showForm && (
        <InstanceForm
          instance={editing}
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
