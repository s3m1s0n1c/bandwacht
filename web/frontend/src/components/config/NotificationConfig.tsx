import { useCallback, useEffect, useState } from 'react'
import { Plus, Trash2, Send } from 'lucide-react'
import { notifications as api } from '../../api/client'
import { UI } from '../../utils/strings'
import StatusBadge from '../shared/StatusBadge'
import ConfirmDialog from '../shared/ConfirmDialog'
import type { NotificationConfig as NotifType } from '../../types'

const BACKENDS = [
  { value: 'console', label: 'Konsole' },
  { value: 'gotify', label: 'Gotify', fields: ['url', 'token'] },
  { value: 'telegram', label: 'Telegram', fields: ['bot_token', 'chat_id'] },
  { value: 'ntfy', label: 'ntfy', fields: ['topic', 'server'] },
  { value: 'webhook', label: 'Webhook', fields: ['url'] },
]

export default function NotificationConfig() {
  const [configs, setConfigs] = useState<NotifType[]>([])
  const [deleteId, setDeleteId] = useState<number | null>(null)
  const [addBackend, setAddBackend] = useState('')
  const [testing, setTesting] = useState<number | null>(null)

  const load = useCallback(async () => {
    const data = await api.list()
    setConfigs(data)
  }, [])

  useEffect(() => { load() }, [load])

  const handleAdd = async () => {
    if (!addBackend) return
    await api.create({ backend: addBackend, enabled: true, config_json: {} })
    setAddBackend('')
    load()
  }

  const handleDelete = async () => {
    if (deleteId == null) return
    await api.delete(deleteId)
    setDeleteId(null)
    load()
  }

  const handleToggle = async (cfg: NotifType) => {
    await api.update(cfg.id, { enabled: !cfg.enabled })
    load()
  }

  const handleTest = async (id: number) => {
    setTesting(id)
    try {
      await api.test(id)
    } catch {
      // ignore
    } finally {
      setTesting(null)
    }
  }

  const handleConfigChange = async (cfg: NotifType, key: string, value: string) => {
    const newConfig = { ...cfg.config_json, [key]: value }
    await api.update(cfg.id, { config_json: newConfig })
    load()
  }

  return (
    <>
      <div className="flex items-center gap-2 mb-3">
        <select className="input" value={addBackend} onChange={e => setAddBackend(e.target.value)}>
          <option value="">Backend wählen...</option>
          {BACKENDS.map(b => (
            <option key={b.value} value={b.value}>{b.label}</option>
          ))}
        </select>
        <button onClick={handleAdd} disabled={!addBackend} className="btn-primary flex items-center gap-1.5">
          <Plus className="w-3.5 h-3.5" />
          Hinzufügen
        </button>
      </div>

      <div className="space-y-3">
        {configs.map(cfg => {
          const backendDef = BACKENDS.find(b => b.value === cfg.backend)
          return (
            <div key={cfg.id} className="p-3 bg-sdr-bg rounded-lg border border-sdr-border space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <StatusBadge active={cfg.enabled} />
                  <span className="text-sm font-medium">{backendDef?.label ?? cfg.backend}</span>
                </div>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => handleToggle(cfg)}
                    className="btn-ghost text-xs px-2 py-1"
                  >
                    {cfg.enabled ? 'Deaktivieren' : 'Aktivieren'}
                  </button>
                  <button
                    onClick={() => handleTest(cfg.id)}
                    disabled={testing === cfg.id}
                    className="p-1.5 text-sdr-muted hover:text-sdr-cyan transition-colors"
                    title={UI.cfg_test}
                  >
                    <Send className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => setDeleteId(cfg.id)}
                    className="p-1.5 text-sdr-muted hover:text-sdr-red transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {backendDef?.fields && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {backendDef.fields.map(field => (
                    <div key={field}>
                      <label className="label">{field}</label>
                      <input
                        className="input w-full"
                        value={(cfg.config_json as Record<string, string>)[field] ?? ''}
                        onChange={e => handleConfigChange(cfg, field, e.target.value)}
                        onBlur={e => handleConfigChange(cfg, field, e.target.value)}
                        placeholder={field}
                      />
                    </div>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>

      <ConfirmDialog
        open={deleteId != null}
        message={UI.confirm_delete}
        onConfirm={handleDelete}
        onCancel={() => setDeleteId(null)}
      />
    </>
  )
}
