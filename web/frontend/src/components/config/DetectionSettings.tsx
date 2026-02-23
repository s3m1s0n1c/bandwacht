import { useCallback, useEffect, useState } from 'react'
import { settings as api } from '../../api/client'
import { UI } from '../../utils/strings'
import DecibelSlider from '../shared/DecibelSlider'
import type { GlobalSettings } from '../../types'

export default function DetectionSettings() {
  const [data, setData] = useState<GlobalSettings | null>(null)
  const [saving, setSaving] = useState(false)

  const load = useCallback(async () => {
    const s = await api.get()
    setData(s)
  }, [])

  useEffect(() => { load() }, [load])

  const save = async () => {
    if (!data) return
    setSaving(true)
    try {
      const result = await api.update(data)
      setData(result)
    } finally {
      setSaving(false)
    }
  }

  if (!data) return <p className="text-sdr-muted text-sm">{UI.loading}</p>

  return (
    <div className="space-y-4">
      <DecibelSlider
        value={data.threshold_db}
        onChange={v => setData({ ...data, threshold_db: v })}
        label={UI.cfg_threshold}
      />

      <DecibelSlider
        value={data.hysteresis_db}
        onChange={v => setData({ ...data, hysteresis_db: v })}
        label={UI.cfg_hysteresis}
        min={0}
        max={20}
      />

      <div>
        <label className="label">{UI.cfg_hold_time}</label>
        <input
          type="number"
          step="0.5"
          min="0"
          value={data.hold_time_s}
          onChange={e => setData({ ...data, hold_time_s: parseFloat(e.target.value) })}
          className="input w-32"
        />
      </div>

      <div>
        <label className="label">{UI.cfg_cooldown}</label>
        <input
          type="number"
          step="1"
          min="0"
          value={data.cooldown_s}
          onChange={e => setData({ ...data, cooldown_s: parseFloat(e.target.value) })}
          className="input w-32"
        />
      </div>

      <label className="flex items-center gap-2 text-sm cursor-pointer">
        <input
          type="checkbox"
          checked={data.record_enabled}
          onChange={e => setData({ ...data, record_enabled: e.target.checked })}
          className="accent-sdr-cyan"
        />
        {UI.cfg_record}
      </label>

      <label className="flex items-center gap-2 text-sm cursor-pointer">
        <input
          type="checkbox"
          checked={data.scan_full_band}
          onChange={e => setData({ ...data, scan_full_band: e.target.checked })}
          className="accent-sdr-cyan"
        />
        {UI.cfg_scan_full}
      </label>

      <div className="pt-2">
        <button onClick={save} disabled={saving} className="btn-primary">
          {saving ? UI.loading : UI.cfg_save}
        </button>
      </div>
    </div>
  )
}
