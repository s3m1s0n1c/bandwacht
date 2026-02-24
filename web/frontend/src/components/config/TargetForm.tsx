import { useState } from 'react'
import { X } from 'lucide-react'
import { targets as api } from '../../api/client'
import { UI } from '../../utils/strings'
import FrequencyInput from '../shared/FrequencyInput'
import DecibelSlider from '../shared/DecibelSlider'
import type { SdrInstance, WatchTarget } from '../../types'

interface TargetFormProps {
  target: WatchTarget | null
  instances: SdrInstance[]
  onClose: () => void
  onSaved: () => void
}

export default function TargetForm({ target, instances, onClose, onSaved }: TargetFormProps) {
  const [instanceId, setInstanceId] = useState<number | null>(target?.instance_id ?? null)
  const [freqHz, setFreqHz] = useState(target?.freq_hz ?? 145_500_000)
  const [bandwidthHz, setBandwidthHz] = useState(target?.bandwidth_hz ?? 12000)
  const [label, setLabel] = useState(target?.label ?? '')
  const [thresholdDb, setThresholdDb] = useState(target?.threshold_db ?? -55)
  const [enabled, setEnabled] = useState(target?.enabled ?? true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      if (target) {
        await api.update(target.id, {
          freq_hz: freqHz,
          bandwidth_hz: bandwidthHz,
          label,
          threshold_db: thresholdDb,
          enabled,
        })
      } else {
        await api.create({
          instance_id: instanceId,
          freq_hz: freqHz,
          bandwidth_hz: bandwidthHz,
          label,
          threshold_db: thresholdDb,
          enabled,
        })
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
            {target ? 'Ziel bearbeiten' : UI.cfg_add_target}
          </h3>
          <button type="button" onClick={onClose} className="text-sdr-muted hover:text-sdr-text">
            <X className="w-4 h-4" />
          </button>
        </div>

        {error && <p className="text-sdr-red text-xs">{error}</p>}

        {!target && (
          <div>
            <label className="label">SDR-Instanz</label>
            <select className="input w-full" value={instanceId ?? ''} onChange={e => setInstanceId(e.target.value === '' ? null : Number(e.target.value))}>
              <option value="">{UI.cfg_global_target}</option>
              {instances.map(i => (
                <option key={i.id} value={i.id}>{i.name}</option>
              ))}
            </select>
          </div>
        )}

        <FrequencyInput value={freqHz} onChange={setFreqHz} label={UI.cfg_freq} />

        <div>
          <label className="label">{UI.cfg_bandwidth}</label>
          <div className="relative">
            <input
              type="number"
              step="0.1"
              value={bandwidthHz / 1000}
              onChange={e => setBandwidthHz(parseFloat(e.target.value) * 1000)}
              className="input w-full pr-12"
            />
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-sdr-muted">kHz</span>
          </div>
        </div>

        <div>
          <label className="label">{UI.cfg_label}</label>
          <input className="input w-full" value={label} onChange={e => setLabel(e.target.value)} placeholder="z.B. OE8XKK Ausgabe" />
        </div>

        <DecibelSlider value={thresholdDb} onChange={setThresholdDb} label={UI.cfg_threshold} />

        <label className="flex items-center gap-2 text-sm cursor-pointer">
          <input type="checkbox" checked={enabled} onChange={e => setEnabled(e.target.checked)} className="accent-sdr-cyan" />
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
