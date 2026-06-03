import { describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

const loadMock = vi.fn().mockResolvedValue(undefined)
const renderMock = vi.fn()

vi.mock('opensheetmusicdisplay', () => ({
  OpenSheetMusicDisplay: vi.fn(function MockOSMD() {
    return {
      load: loadMock,
      render: renderMock,
      zoom: 1,
    }
  }),
}))

import { ScoreViewer } from './ScoreViewer'

describe('ScoreViewer', () => {
  it('renders a friendly message when musicXml is empty', () => {
    render(<ScoreViewer musicXml={null} />)

    expect(screen.getByText(/your score will appear here/i)).toBeInTheDocument()
  })

  it('renders score container and zoom controls for valid musicXml', async () => {
    const user = userEvent.setup()
    const { rerender } = render(<ScoreViewer musicXml={null} />)

    rerender(<ScoreViewer musicXml={'<score-partwise version="3.1"></score-partwise>'} />)

    expect(screen.getByText('SATB score')).toBeInTheDocument()
    await waitFor(() => expect(loadMock).toHaveBeenCalled())
    await user.click(screen.getByRole('button', { name: /zoom in/i }))
    expect(screen.getByText('90%')).toBeInTheDocument()
  })

  it('shows error message when error prop is provided', () => {
    render(<ScoreViewer musicXml={null} error="Score is not ready yet." />)

    expect(screen.getByText(/score unavailable/i)).toBeInTheDocument()
    expect(screen.getByText('Score is not ready yet.')).toBeInTheDocument()
  })
})
