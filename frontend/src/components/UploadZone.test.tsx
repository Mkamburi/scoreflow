import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { UploadZone } from './UploadZone'

describe('UploadZone', () => {
  it('renders upload instructions', () => {
    render(
      <UploadZone
        uploadState={{ phase: 'idle' }}
        onFileSelected={vi.fn()}
        onReset={vi.fn()}
      />,
    )

    expect(screen.getByText(/drop a wav file here/i)).toBeInTheDocument()
  })

  it('calls onFileSelected when a wav file is chosen', async () => {
    const user = userEvent.setup()
    const onFileSelected = vi.fn()

    render(
      <UploadZone
        uploadState={{ phase: 'idle' }}
        onFileSelected={onFileSelected}
        onReset={vi.fn()}
      />,
    )

    const file = new File(['fake-wav'], 'demo.wav', { type: 'audio/wav' })
    const input = document.querySelector('input[type="file"]') as HTMLInputElement

    await user.upload(input, file)

    expect(onFileSelected).toHaveBeenCalledWith(file)
  })
})
