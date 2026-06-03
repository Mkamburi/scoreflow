// AI-assisted: Milestone 3.5 playback controls — play/pause and tempo for edited score.

import type Embed from 'flat-embed'
import { useCallback, useEffect, useState } from 'react'

interface PlaybackControlsProps {
  embed: Embed | null
}

export function PlaybackControls({ embed }: PlaybackControlsProps) {
  const [isPlaying, setIsPlaying] = useState(false)
  const [speed, setSpeed] = useState(1)

  useEffect(() => {
    if (!embed) {
      setIsPlaying(false)
      return
    }

    const handlePlay = () => setIsPlaying(true)
    const handlePause = () => setIsPlaying(false)
    const handleStop = () => setIsPlaying(false)

    embed.on('play', handlePlay)
    embed.on('pause', handlePause)
    embed.on('stop', handleStop)

    return () => {
      embed.off('play', handlePlay)
      embed.off('pause', handlePause)
      embed.off('stop', handleStop)
    }
  }, [embed])

  const togglePlayback = useCallback(async () => {
    if (!embed) {
      return
    }

    if (isPlaying) {
      await embed.pause()
      return
    }

    await embed.play()
  }, [embed, isPlaying])

  const handleSpeedChange = useCallback(
    async (nextSpeed: number) => {
      setSpeed(nextSpeed)
      if (embed) {
        await embed.setPlaybackSpeed(nextSpeed)
      }
    },
    [embed],
  )

  if (!embed) {
    return null
  }

  return (
    <div className="mt-4 flex flex-wrap items-center gap-3 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
      <button
        type="button"
        aria-label={isPlaying ? 'Pause playback' : 'Play score'}
        onClick={() => void togglePlayback()}
        className="rounded-lg bg-violet-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-violet-700"
      >
        {isPlaying ? 'Pause' : 'Play'}
      </button>

      <label className="flex items-center gap-2 text-sm text-slate-700">
        Tempo
        <select
          aria-label="Playback tempo"
          value={speed}
          onChange={(event) => void handleSpeedChange(Number(event.target.value))}
          className="rounded-lg border border-slate-300 bg-white px-2 py-1"
        >
          <option value={0.5}>50%</option>
          <option value={0.75}>75%</option>
          <option value={1}>100%</option>
          <option value={1.25}>125%</option>
          <option value={1.5}>150%</option>
        </select>
      </label>
    </div>
  )
}
