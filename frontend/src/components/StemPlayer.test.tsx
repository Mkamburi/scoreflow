import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { StemPlayer } from './StemPlayer'

describe('StemPlayer', () => {
  it('renders audio players for completed jobs with stems', () => {
    render(
      <StemPlayer
        jobStatus={{
          job_id: 'abc-123',
          status: 'completed',
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
        }}
      />,
    )

    expect(screen.getByText(/listen to separated stems/i)).toBeInTheDocument()
    expect(screen.getByText('Vocals')).toBeInTheDocument()
    expect(document.querySelectorAll('audio')).toHaveLength(4)
    expect(screen.getAllByText(/download wav/i)).toHaveLength(4)
  })
})
