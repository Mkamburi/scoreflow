// AI-assisted: Floating pill transport dock — circular neumorphic rewind / play / forward.

import type Embed from 'flat-embed'
import { useCallback, useEffect, useRef, useState } from 'react'

import type { StemTrackId } from '../theme/stems'
import { STEM_TRACK_STYLES } from '../theme/stems'

interface TransportBarProps {
  flatEmbed?: Embed | null
  selectedStem: StemTrackId | null
  jobId: string | null
}

function RewindIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
      <path d="M11 18V6l-8.5 6 8.5 6zm.5-6l8.5 6V6l-8.5 6z" />
    </svg>
  )
}

function ForwardIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
      <path d="M4 18l8.5-6L4 6v12zm9-12v12l8.5-6L13 6z" />
    </svg>
  )
}

function PlayIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
      <path d="M8 5v14l11-7z" />
    </svg>
  )
}

function PauseIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
      <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z" />
    </svg>
  )
}

export function TransportBar({ flatEmbed, selectedStem, jobId }: TransportBarProps) {
  const [isPlaying, setIsPlaying] = useState(false)
  const [speed, setSpeed] = useState(1)
  const stemAudioRef = useRef<HTMLAudioElement | null>(null)

  useEffect(() => {
    if (!jobId || !selectedStem) {
      stemAudioRef.current = null
      return
    }

    const element = document.querySelector<HTMLAudioElement>(`audio[data-stem="${selectedStem}"]`)
    stemAudioRef.current = element
  }, [jobId, selectedStem])

  useEffect(() => {
    if (!flatEmbed) {
      return
    }

    const handlePlay = () => setIsPlaying(true)
    const handlePause = () => setIsPlaying(false)
    const handleStop = () => setIsPlaying(false)

    flatEmbed.on('play', handlePlay)
    flatEmbed.on('pause', handlePause)
    flatEmbed.on('stop', handleStop)

    return () => {
      flatEmbed.off('play', handlePlay)
      flatEmbed.off('pause', handlePause)
      flatEmbed.off('stop', handleStop)
    }
  }, [flatEmbed])

  const stopFlatPlayback = useCallback(async () => {
    if (!flatEmbed) {
      return
    }
    try {
      await flatEmbed.stop()
    } catch {
      // stop() ends note previews; pause() alone can leave a clicked note ringing
    }
    try {
      await flatEmbed.pause()
    } catch {
      // ignore
    }
    setIsPlaying(false)
  }, [flatEmbed])

  const togglePlayback = useCallback(async () => {
    if (flatEmbed && !selectedStem) {
      if (isPlaying) {
        await stopFlatPlayback()
      } else {
        await flatEmbed.play()
        setIsPlaying(true)
      }
      return
    }

    const audio = stemAudioRef.current
    if (!audio) {
      return
    }

    if (isPlaying) {
      audio.pause()
      setIsPlaying(false)
      return
    }

    try {
      await audio.play()
      setIsPlaying(true)
    } catch {
      setIsPlaying(false)
    }
  }, [flatEmbed, isPlaying, selectedStem, stopFlatPlayback])

  useEffect(() => {
    const audio = stemAudioRef.current
    if (!audio) {
      return
    }

    const handleEnded = () => setIsPlaying(false)
    const handlePlay = () => setIsPlaying(true)
    const handlePause = () => setIsPlaying(false)
    audio.addEventListener('ended', handleEnded)
    audio.addEventListener('play', handlePlay)
    audio.addEventListener('pause', handlePause)
    return () => {
      audio.removeEventListener('ended', handleEnded)
      audio.removeEventListener('play', handlePlay)
      audio.removeEventListener('pause', handlePause)
    }
  }, [selectedStem, jobId])

  const seekStem = useCallback((deltaSeconds: number) => {
    const audio = stemAudioRef.current
    if (!audio) {
      return
    }

    const duration = Number.isFinite(audio.duration) ? audio.duration : 0
    const next = Math.min(Math.max(0, audio.currentTime + deltaSeconds), duration || Infinity)
    audio.currentTime = next
  }, [])

  const handleRewind = useCallback(() => {
    if (selectedStem) {
      seekStem(-5)
      return
    }
    void stopFlatPlayback()
  }, [seekStem, selectedStem, stopFlatPlayback])

  const handleForward = useCallback(() => {
    if (selectedStem) {
      seekStem(5)
      return
    }
    void flatEmbed?.play()
  }, [flatEmbed, seekStem, selectedStem])

  const handleSpeedChange = useCallback(
    async (nextSpeed: number) => {
      setSpeed(nextSpeed)
      if (flatEmbed && !selectedStem) {
        await flatEmbed.setPlaybackSpeed(nextSpeed)
        return
      }

      const audio = stemAudioRef.current
      if (audio) {
        audio.playbackRate = nextSpeed
      }
    },
    [flatEmbed, selectedStem],
  )

  const transportDisabled = !flatEmbed && !selectedStem
  const stemLabel = selectedStem ? STEM_TRACK_STYLES[selectedStem].label : null

  return (
    <div className="pointer-events-none fixed inset-x-0 bottom-5 z-50 flex justify-center px-4">
      <div className="sf-transport-dock pointer-events-auto flex flex-wrap items-center gap-4 px-6 py-3">
        <div className="flex items-center gap-3">
          <button
            type="button"
            aria-label="Rewind 5 seconds"
            onClick={handleRewind}
            disabled={transportDisabled}
            className="sf-neu-btn-round"
          >
            <RewindIcon />
          </button>

          <button
            type="button"
            aria-label={isPlaying ? 'Pause' : 'Play'}
            onClick={() => void togglePlayback()}
            disabled={transportDisabled}
            className={[
              'sf-neu-btn-round sf-neu-btn-round--lg',
              isPlaying ? 'sf-neu-btn-round--active' : '',
            ].join(' ')}
          >
            {isPlaying ? <PauseIcon /> : <PlayIcon />}
          </button>

          <button
            type="button"
            aria-label="Forward 5 seconds"
            onClick={handleForward}
            disabled={transportDisabled}
            className="sf-neu-btn-round"
          >
            <ForwardIcon />
          </button>
        </div>

        <label className="sf-label flex items-center gap-2 normal-case tracking-normal">
          <span className="text-[var(--color-sf-text-muted)]">Tempo</span>
          <select
            aria-label="Playback tempo"
            value={speed}
            onChange={(event) => void handleSpeedChange(Number(event.target.value))}
            className="sf-select"
          >
            <option value={0.5}>50%</option>
            <option value={0.75}>75%</option>
            <option value={1}>100%</option>
            <option value={1.25}>125%</option>
            <option value={1.5}>150%</option>
          </select>
        </label>

        <span className="sf-mono text-xs text-[var(--color-sf-text-muted)]">
          {stemLabel ? (
            <>
              Stem: <span className="text-[var(--color-sf-orange)]">{stemLabel}</span>
            </>
          ) : flatEmbed ? (
            'Score playback'
          ) : (
            'Select a track'
          )}
        </span>
      </div>
    </div>
  )
}
