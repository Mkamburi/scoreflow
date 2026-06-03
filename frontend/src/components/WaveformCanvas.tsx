// AI-assisted: Waveform visualization — orange accent on sandy neumorphic base.

import { useEffect, useRef } from 'react'

interface WaveformCanvasProps {
  peaks: number[]
  opacity?: number
  height?: number
  variant?: 'linear' | 'radial'
}

export function WaveformCanvas({
  peaks,
  opacity = 1,
  height = 56,
  variant = 'linear',
}: WaveformCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) {
      return
    }

    const context = canvas.getContext('2d')
    if (!context) {
      return
    }

    const width = canvas.clientWidth
    const deviceRatio = window.devicePixelRatio || 1
    canvas.width = width * deviceRatio
    canvas.height = height * deviceRatio
    context.scale(deviceRatio, deviceRatio)
    context.clearRect(0, 0, width, height)

    if (variant === 'radial') {
      const centerX = width / 2
      const centerY = height / 2
      const maxRadius = Math.min(centerX, centerY) * 0.85
      const step = Math.max(peaks.length, 1)

      peaks.forEach((peak, index) => {
        const angle = (index / step) * Math.PI * 2 - Math.PI / 2
        const radius = maxRadius * (0.35 + peak * 0.65)
        const depth = 0.4 + peak * 0.6
        context.strokeStyle = `rgba(232, 93, 4, ${depth * opacity})`
        context.lineWidth = 2.5
        context.beginPath()
        context.moveTo(
          centerX + Math.cos(angle) * maxRadius * 0.25,
          centerY + Math.sin(angle) * maxRadius * 0.25,
        )
        context.lineTo(centerX + Math.cos(angle) * radius, centerY + Math.sin(angle) * radius)
        context.stroke()
      })
      return
    }

    const barWidth = width / Math.max(peaks.length, 1)
    const centerY = height / 2

    peaks.forEach((peak, index) => {
      const barHeight = Math.max(2, peak * (height * 0.42))
      const depth = 0.35 + peak * 0.65
      context.fillStyle = `rgba(232, 93, 4, ${depth * opacity})`
      const x = index * barWidth
      context.fillRect(x, centerY - barHeight, Math.max(1, barWidth - 1), barHeight * 2)
    })
  }, [peaks, opacity, height, variant])

  return (
    <canvas
      ref={canvasRef}
      className="w-full"
      style={{ height }}
      role="img"
      aria-label="Audio waveform"
    />
  )
}

export function WaveformPlaceholder({ opacity = 0.3, height = 56 }: { opacity?: number; height?: number }) {
  const placeholderPeaks = Array.from({ length: 80 }, (_, index) => {
    return 0.2 + Math.abs(Math.sin(index * 0.35)) * 0.5
  })

  return <WaveformCanvas peaks={placeholderPeaks} opacity={opacity} height={height} />
}
