import { useCallback, useEffect, useRef } from 'react'

interface SpectrumDisplayProps {
  fftData: number[] | null
  centerFreq: number
  bandwidth: number
  className?: string
}

const GRID_COLOR = '#1f2937'
const SPECTRUM_COLOR = '#00ff41'
const FILL_COLOR = 'rgba(0, 255, 65, 0.08)'
const LABEL_COLOR = '#9ca3af'

/** Compute percentile value from sorted array */
function percentile(sorted: number[], p: number): number {
  const idx = (p / 100) * (sorted.length - 1)
  const lo = Math.floor(idx)
  const hi = Math.ceil(idx)
  if (lo === hi) return sorted[lo]
  return sorted[lo] + (sorted[hi] - sorted[lo]) * (idx - lo)
}

export default function SpectrumDisplay({ fftData, centerFreq, bandwidth, className = '' }: SpectrumDisplayProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const prevData = useRef<number[] | null>(null)
  // Smoothed display range for stable rendering
  const rangeRef = useRef<{ min: number; max: number } | null>(null)

  const draw = useCallback(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const rect = canvas.getBoundingClientRect()
    const dpr = window.devicePixelRatio || 1
    canvas.width = rect.width * dpr
    canvas.height = rect.height * dpr
    ctx.scale(dpr, dpr)

    const w = rect.width
    const h = rect.height
    const padding = { top: 10, right: 10, bottom: 30, left: 50 }
    const plotW = w - padding.left - padding.right
    const plotH = h - padding.top - padding.bottom

    // Clear
    ctx.fillStyle = '#0a0e17'
    ctx.fillRect(0, 0, w, h)

    // Smoothing between frames
    const data = fftData ?? prevData.current
    if (data) prevData.current = data
    if (!data || data.length === 0) return

    // Auto-scale: use percentiles to find stable display range
    const sorted = [...data].sort((a, b) => a - b)
    const p5 = percentile(sorted, 2)
    const p95 = percentile(sorted, 98)
    const margin = Math.max(Math.abs(p95 - p5) * 0.1, 10)

    const targetMin = p5 - margin
    const targetMax = p95 + margin

    // Smooth transitions (exponential moving average)
    const alpha = rangeRef.current ? 0.1 : 1.0
    if (!rangeRef.current) {
      rangeRef.current = { min: targetMin, max: targetMax }
    } else {
      rangeRef.current.min += (targetMin - rangeRef.current.min) * alpha
      rangeRef.current.max += (targetMax - rangeRef.current.max) * alpha
    }

    const valMin = rangeRef.current.min
    const valMax = rangeRef.current.max
    const valRange = valMax - valMin || 1

    // Grid lines (5 evenly spaced)
    ctx.strokeStyle = GRID_COLOR
    ctx.lineWidth = 0.5
    const gridSteps = 5
    for (let i = 0; i <= gridSteps; i++) {
      const val = valMin + (valRange / gridSteps) * i
      const y = padding.top + plotH * (1 - i / gridSteps)
      ctx.beginPath()
      ctx.moveTo(padding.left, y)
      ctx.lineTo(padding.left + plotW, y)
      ctx.stroke()

      ctx.fillStyle = LABEL_COLOR
      ctx.font = '10px monospace'
      ctx.textAlign = 'right'
      ctx.fillText(`${Math.round(val)}`, padding.left - 5, y + 3)
    }

    // Frequency labels
    const startFreq = centerFreq - bandwidth / 2
    const steps = 5
    ctx.textAlign = 'center'
    for (let i = 0; i <= steps; i++) {
      const freq = startFreq + (bandwidth / steps) * i
      const x = padding.left + (plotW / steps) * i
      ctx.fillStyle = LABEL_COLOR
      ctx.fillText(`${(freq / 1e6).toFixed(2)}`, x, h - 5)
    }

    // Draw spectrum
    ctx.beginPath()
    ctx.strokeStyle = SPECTRUM_COLOR
    ctx.lineWidth = 1.5

    const binStep = plotW / data.length
    for (let i = 0; i < data.length; i++) {
      const x = padding.left + i * binStep
      const clamped = Math.max(valMin, Math.min(valMax, data[i]))
      const y = padding.top + plotH * (1 - (clamped - valMin) / valRange)
      if (i === 0) ctx.moveTo(x, y)
      else ctx.lineTo(x, y)
    }
    ctx.stroke()

    // Fill under curve
    ctx.lineTo(padding.left + plotW, padding.top + plotH)
    ctx.lineTo(padding.left, padding.top + plotH)
    ctx.closePath()
    ctx.fillStyle = FILL_COLOR
    ctx.fill()
  }, [fftData, centerFreq, bandwidth])

  useEffect(() => {
    draw()
  }, [draw])

  useEffect(() => {
    const handleResize = () => draw()
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [draw])

  return (
    <canvas
      ref={canvasRef}
      className={`w-full rounded-lg ${className}`}
      style={{ height: '256px' }}
    />
  )
}
