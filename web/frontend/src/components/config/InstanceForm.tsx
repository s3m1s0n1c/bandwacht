import { useState } from 'react'
import { X } from 'lucide-react'
import { instances as api } from '../../api/client'
import { UI } from '../../utils/strings'
import type { SdrInstance } from '../../types'

interface InstanceFormProps {
  instance: SdrInstance | null
  onClose: () => void
  onSaved: () => void
}

export default function InstanceForm({ instance, onClose, onSaved }: InstanceFormProps) {
  const [name, setName] = useState(instance?.name ?? '')
  const [url, setUrl] = useState(instance?.url ?? '')
  const [enabled, setEnabled] = useState(instance?.enabled ?? true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      if (instance) {
        await api.update(instance.id, { name, url, enabled })
      } else {
        await api.create({ name, url, enabled })
      }
      onSaved()
    } catch (err: any) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
      <form onSubmit={handleSubmit} className="card max-w-md w-full space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-medium">
            {instance ? 'Instanz bearbeiten' : UI.cfg_add_instance}
          </h3>
          <button type="button" onClick={onClose} className="text-sdr-muted hover:text-sdr-text">
            <X className="w-4 h-4" />
          </button>
        </div>

        {error && <p className="text-sdr-red text-xs">{error}</p>}

        <div>
          <label className="label">{UI.cfg_name}</label>
          <input className="input w-full" value={name} onChange={e => setName(e.target.value)} required />
        </div>

        <div>
          <label className="label">{UI.cfg_url}</label>
          <input className="input w-full" value={url} onChange={e => setUrl(e.target.value)} placeholder="http://sdr-host:8073" required />
        </div>

        <label className="flex items-center gap-2 text-sm cursor-pointer">
          <input type="checkbox" checked={enabled} onChange={e => setEnabled(e.target.checked)}
            className="accent-sdr-cyan" />
          {UI.cfg_enabled}
        </label>

        <div className="flex justify-end gap-2 pt-2">
          <button type="button" onClick={onClose} className="btn-ghost">{UI.cfg_cancel}</button>
          <button type="submit" disabled={saving} className="btn-primary">
            {saving ? UI.loading : UI.cfg_save}
          </button>
        </div>
      </form>
    </div>
  )
}
