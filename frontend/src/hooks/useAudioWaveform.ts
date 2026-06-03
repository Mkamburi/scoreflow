// AI-assisted: Decode stem audio into peak buckets for orange waveform rendering.

import { useEffect, useState } from 'react'

const BUCKET_COUNT = 120

export function useAudioWaveform(audioUrl: string | null): number[] {
  const [peaks, setPeaks] = useState<number[]>([])

  useEffect(() => {
    if (!audioUrl) {
      setPeaks([])
      return
    }

    let cancelled = false
    const audioContext = new AudioContext()

    const load = async () => {
      try {
        const response = await fetch(audioUrl)
        const buffer = await response.arrayBuffer()
        const audioBuffer = await audioContext.decodeAudioData(buffer.slice(0))
        const channel = audioBuffer.getChannelData(0)
        const blockSize = Math.floor(channel.length / BUCKET_COUNT) || 1
        const nextPeaks: number[] = []

        for (let index = 0; index < BUCKET_COUNT; index += 1) {
          const start = index * blockSize
          let peak = 0
          for (let sample = start; sample < start + blockSize && sample < channel.length; sample += 1) {
            peak = Math.max(peak, Math.abs(channel[sample]))
          }
          nextPeaks.push(peak)
        }

        const maxPeak = Math.max(...nextPeaks, 0.001)
        if (!cancelled) {
          setPeaks(nextPeaks.map((value) => value / maxPeak))
        }
      } catch {
        if (!cancelled) {
          setPeaks([])
        }
      } finally {
        void audioContext.close()
      }
    }

    void load()

    return () => {
      cancelled = true
      void audioContext.close()
    }
  }, [audioUrl])

  return peaks
}
