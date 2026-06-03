import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'

const loadMusicXmlMock = vi.fn().mockResolvedValue(undefined)
const getMusicXmlMock = vi.fn().mockResolvedValue('<score-partwise version="3.1"></score-partwise>')

vi.mock('flat-embed', () => ({
  default: vi.fn(function MockEmbed() {
    return {
      ready: vi.fn().mockResolvedValue(undefined),
      loadMusicXML: loadMusicXmlMock,
      getMusicXML: getMusicXmlMock,
      on: vi.fn(),
      off: vi.fn(),
    }
  }),
}))

afterEach(() => {
  vi.unstubAllEnvs()
})

describe('ScoreEditor', () => {
  it('shows setup instructions when Flat app id is missing', async () => {
    vi.stubEnv('VITE_FLAT_APP_ID', '')
    const { ScoreEditor, isFlatEditorConfigured } = await import('./ScoreEditor')

    render(
      <ScoreEditor
        musicXml={'<score-partwise version="3.1"></score-partwise>'}
        reloadKey={0}
        onScoreChange={vi.fn()}
      />,
    )

    expect(screen.getByText(/flat.io editor not configured/i)).toBeInTheDocument()
    expect(isFlatEditorConfigured()).toBe(false)
  })

  it('mounts the Flat embed container when app id is configured', async () => {
    vi.stubEnv('VITE_FLAT_APP_ID', 'test-app-id')
    const { ScoreEditor, isFlatEditorConfigured } = await import('./ScoreEditor')

    render(
      <ScoreEditor
        musicXml={'<score-partwise version="3.1"></score-partwise>'}
        reloadKey={0}
        onScoreChange={vi.fn()}
      />,
    )

    expect(screen.getByTestId('flat-editor-container')).toBeInTheDocument()
    expect(isFlatEditorConfigured()).toBe(true)
  })
})

describe('EditorToolbar', () => {
  it('calls undo when the undo button is clicked', async () => {
    const onUndo = vi.fn()
    const { EditorToolbar } = await import('./EditorToolbar')
    const user = userEvent.setup()

    render(
      <EditorToolbar canUndo canRedo={false} onUndo={onUndo} onRedo={vi.fn()} isEditorActive />,
    )

    await user.click(screen.getByRole('button', { name: /undo/i }))
    expect(onUndo).toHaveBeenCalledTimes(1)
  })
})
