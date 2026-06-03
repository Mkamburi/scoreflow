// AI-assisted: DAW track stack — neumorphic cards with pressed inset when playing.

import { useCallback, useEffect, useRef } from 'react'

import type { JobStatusResponse } from '../types/pipeline'
import { getStemDownloadUrl, getStemStreamUrl } from '../api/stems'
import { useAudioWaveform } from '../hooks/useAudioWaveform'
import { STEM_TRACK_ORDER, STEM_TRACK_STYLES, type StemTrackId } from '../theme/stems'
import { WaveformCanvas, WaveformPlaceholder } from './WaveformCanvas'

interface DawTrackStackProps {
  jobStatus: JobStatusResponse
  playingStem: StemTrackId | null
  onPlayStem: (stem: StemTrackId | null) => void
}

function pauseAllStemAudio(except?: StemTrackId) {
  document.querySelectorAll<HTMLAudioElement>('audio[data-stem]').forEach((audio) => {
    if (except && audio.dataset.stem === except) {
      return
    }
    audio.pause()
  })
}

function TrackRow({
  jobId,
  stem,
  isPlaying,
  onTogglePlay,
}: {
  jobId: string
  stem: StemTrackId
  isPlaying: boolean
  onTogglePlay: (stem: StemTrackId) => void
}) {
  const style = STEM_TRACK_STYLES[stem]
  const streamUrl = getStemStreamUrl(jobId, stem)
  const peaks = useAudioWaveform(streamUrl)
  const audioRef = useRef<HTMLAudioElement>(null)

  useEffect(() => {
    const audio = audioRef.current
    if (!audio) {
      return
    }

    const handleEnded = () => onTogglePlay(stem)
    audio.addEventListener('ended', handleEnded)
    return () => audio.removeEventListener('ended', handleEnded)
  }, [onTogglePlay, stem])

  useEffect(() => {
    const audio = audioRef.current
    if (!audio) {
      return
    }

    if (!isPlaying) {
      audio.pause()
    }
  }, [isPlaying])

  const handlePlayClick = useCallback(() => {
    const audio = audioRef.current
    if (!audio) {
      return
    }

    if (isPlaying) {
      audio.pause()
      onTogglePlay(stem)
      return
    }

    pauseAllStemAudio(stem)
    const playPromise = audio.play()
    if (playPromise && typeof playPromise.then === 'function') {
      void playPromise.then(() => onTogglePlay(stem)).catch(() => {
        audio.pause()
      })
    } else {
      onTogglePlay(stem)
    }
  }, [isPlaying, onTogglePlay, stem])

  return (
    <li
      className={[
        'sf-card-inner flex gap-3 overflow-hidden p-3 transition-[box-shadow]',
        isPlaying ? 'sf-card-inner--selected' : '',
      ].join(' ')}
    >
      <button
        type="button"
        aria-label={isPlaying ? `Pause ${style.label}` : `Play ${style.label}`}
        onClick={handlePlayClick}
        className={[
          'sf-neu-btn-round shrink-0',
          isPlaying ? 'sf-neu-btn-round--active' : '',
        ].join(' ')}
      >
        {isPlaying ? (
          <span className="text-xs font-bold tracking-tighter">❚❚</span>
        ) : (
          <span className="ml-0.5 text-sm">▶</span>
        )}
      </button>

      <div className="min-w-0 flex-1">
        <div className="mb-2 flex items-center justify-between gap-3">
          <span
            className={[
              'text-sm font-semibold',
              isPlaying ? 'text-[var(--color-sf-orange)]' : 'sf-text-muted',
            ].join(' ')}
          >
            {style.label}
          </span>
          <a href={getStemDownloadUrl(jobId, stem)} download={`${stem}.wav`} className="sf-link shrink-0 text-xs">
            Download WAV
          </a>
        </div>

        {peaks.length > 0 ? (
          <WaveformCanvas peaks={peaks} opacity={style.waveOpacity} />
        ) : (
          <WaveformPlaceholder opacity={style.waveOpacity * 0.5} />
        )}
      </div>

      <audio ref={audioRef} data-stem={stem} src={streamUrl} preload="metadata" />
    </li>
  )
}

const PLAYABLE_PIPELINE_STATUSES = new Set(['transcribing', 'notating', 'completed'])

export function DawTrackStack({ jobStatus, playingStem, onPlayStem }: DawTrackStackProps) {
  if (!jobStatus.demucs_stems || !PLAYABLE_PIPELINE_STATUSES.has(jobStatus.status)) {
    return null
  }

  const availableStems = STEM_TRACK_ORDER.filter((stem) => jobStatus.demucs_stems?.[stem])
  const handleTogglePlay = useCallback(
    (stem: StemTrackId) => {
      if (playingStem === stem) {
        pauseAllStemAudio()
        onPlayStem(null)
        return
      }
      onPlayStem(stem)
    },
    [onPlayStem, playingStem],
  )

  return (
    <section className="sf-card mt-6 w-full max-w-3xl p-5 text-left">
      <h2 className="sf-heading text-lg">Track stack</h2>
      <p className="sf-text-muted mt-1 text-sm">Separated stems — play from each row or the transport bar below.</p>

      <ul className="mt-6 space-y-3">
        {availableStems.map((stem) => (
          <TrackRow
            key={stem}
            jobId={jobStatus.job_id}
            stem={stem}
            isPlaying={playingStem === stem}
            onTogglePlay={handleTogglePlay}
          />
        ))}
      </ul>
    </section>
  )
}
