import { useCallback, useEffect, useState } from 'react'
import { Send } from 'lucide-react'
import { notifications as api } from '../../api/client'
import { UI } from '../../utils/strings'
import StatusBadge from '../shared/StatusBadge'
import type { NotificationConfig as NotifType } from '../../types'

const BACKEND_LABELS: Record<string, string> = {
  console: 'Konsole',
  gotify: 'Gotify',
  telegram: 'Telegram',
  ntfy: 'ntfy',
  webhook: 'Webhook',
}

export default function NotificationConfig() {
  const [configs, setConfigs] = useState<NotifType[]>([])
  const [testing, setTesting] = useState<string | null>(null)

  const load = useCallback(async () => {
    const data = await api.list()
    setConfigs(data)
  }, [])

  useEffect(() => { load() }, [load])

  const handleTest = async (backend: string) => {
    setTesting(backend)
    try {
      await api.test(backend)
    } catch (_) {
      // ignore
    } finally {
      setTesting(null)
    }
  }

  return (
    <>
      <p className="text-xs text-sdr-muted mb-3">
        Konfiguration über Umgebungsvariablen (BANDWACHT_NOTIFY_*).
      </p>

      <div className="space-y-2">
        {configs.map(cfg => (
          <div key={cfg.backend} className="p-3 bg-sdr-bg rounded-lg border border-sdr-border flex items-center justify-between">
            <div className="flex items-center gap-2">
              <StatusBadge active={cfg.configured} />
              <span className="text-sm font-medium">{BACKEND_LABELS[cfg.backend] ?? cfg.backend}</span>
            </div>
            {cfg.backend !== 'console' && cfg.configured && (
              <button
                onClick={() => handleTest(cfg.backend)}
                disabled={testing === cfg.backend}
                className="p-1.5 text-sdr-muted hover:text-sdr-cyan transition-colors"
                title={UI.cfg_test}
              >
                <Send className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        ))}
      </div>
    </>
  )
}
