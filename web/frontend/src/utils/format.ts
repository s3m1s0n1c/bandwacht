/** Format frequency in Hz to human-readable MHz string */
export function formatFreqMHz(hz: number): string {
  return (hz / 1_000_000).toFixed(4) + ' MHz'
}

/** Format frequency in Hz to compact display */
export function formatFreqShort(hz: number): string {
  if (hz >= 1_000_000_000) return (hz / 1_000_000_000).toFixed(3) + ' GHz'
  if (hz >= 1_000_000) return (hz / 1_000_000).toFixed(3) + ' MHz'
  if (hz >= 1_000) return (hz / 1_000).toFixed(1) + ' kHz'
  return hz.toFixed(0) + ' Hz'
}

/** Format dB value */
export function formatDb(db: number): string {
  return db.toFixed(1) + ' dB'
}

/** Format duration in seconds */
export function formatDuration(seconds: number): string {
  if (seconds < 1) return (seconds * 1000).toFixed(0) + ' ms'
  if (seconds < 60) return seconds.toFixed(1) + ' s'
  const min = Math.floor(seconds / 60)
  const sec = Math.floor(seconds % 60)
  return `${min}:${sec.toString().padStart(2, '0')} min`
}

/** Format ISO timestamp to German locale */
export function formatTimestamp(iso: string): string {
  return new Date(iso).toLocaleString('de-AT', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

/** Format ISO timestamp to time only */
export function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString('de-AT', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}
