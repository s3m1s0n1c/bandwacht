interface FrequencyInputProps {
  value: number
  onChange: (hz: number) => void
  label?: string
  className?: string
}

export default function FrequencyInput({ value, onChange, label, className = '' }: FrequencyInputProps) {
  const mhz = value / 1_000_000

  return (
    <div className={className}>
      {label && <label className="label">{label}</label>}
      <div className="relative">
        <input
          type="number"
          step="0.001"
          value={mhz || ''}
          onChange={e => {
            const v = parseFloat(e.target.value)
            if (!isNaN(v)) onChange(v * 1_000_000)
          }}
          className="input w-full pr-14"
          placeholder="145.500"
        />
        <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-sdr-muted">MHz</span>
      </div>
    </div>
  )
}
