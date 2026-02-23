interface DecibelSliderProps {
  value: number
  onChange: (db: number) => void
  label?: string
  min?: number
  max?: number
  step?: number
  className?: string
}

export default function DecibelSlider({
  value, onChange, label, min = -120, max = 0, step = 1, className = ''
}: DecibelSliderProps) {
  return (
    <div className={className}>
      {label && <label className="label">{label}</label>}
      <div className="flex items-center gap-3">
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={e => onChange(parseFloat(e.target.value))}
          className="flex-1 accent-sdr-cyan h-1.5"
        />
        <span className="text-sm font-mono text-sdr-cyan w-16 text-right">{value.toFixed(1)} dB</span>
      </div>
    </div>
  )
}
