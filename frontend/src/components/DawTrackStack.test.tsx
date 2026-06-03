import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

vi.mock('../hooks/useAudioWaveform', () => ({
  useAudioWaveform: () => [],
}))

import { DawTrackStack } from './DawTrackStack'

const jobStatus = {
  job_id: 'abc-123',
  status: 'completed' as const,
  original_filename: 'song.wav',
  size_bytes: 1024,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
  demucs_stems: {
    vocals: '/tmp/vocals.wav',
    drums: '/tmp/drums.wav',
    bass: '/tmp/bass.wav',
    other: '/tmp/other.wav',
  },
}

describe('DawTrackStack', () => {
  it('renders per-track play buttons', () => {
    render(<DawTrackStack jobStatus={jobStatus} playingStem={null} onPlayStem={vi.fn()} />)

    expect(screen.getByRole('button', { name: /play vocals/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /play drums/i })).toBeInTheDocument()
  })

  it('calls onPlayStem when play is clicked', async () => {
    const onPlayStem = vi.fn()
    const user = userEvent.setup()

    render(<DawTrackStack jobStatus={jobStatus} playingStem={null} onPlayStem={onPlayStem} />)

    await user.click(screen.getByRole('button', { name: /play vocals/i }))

    expect(onPlayStem).toHaveBeenCalledWith('vocals')
  })
})
