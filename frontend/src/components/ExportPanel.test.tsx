import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { ExportPanel } from './ExportPanel'

vi.mock('../api/export', () => ({
  downloadMusicXmlClient: vi.fn(),
  downloadBlob: vi.fn(),
  exportScore: vi.fn().mockResolvedValue(new Blob(['midi'])),
}))

import { downloadMusicXmlClient } from '../api/export'

describe('ExportPanel', () => {
  it('downloads MusicXML from props without waiting on Flat', async () => {
    const getMusicXml = vi.fn(() => new Promise<string>(() => {}))
    const flatEmbed = { getMusicXML: getMusicXml } as never

    const user = userEvent.setup()
    render(
      <ExportPanel
        musicXml={'<score-partwise version="3.1"></score-partwise>'}
        jobFilename="song.wav"
        flatEmbed={flatEmbed}
      />,
    )

    await user.click(screen.getByRole('button', { name: /musicxml/i }))

    expect(getMusicXml).not.toHaveBeenCalled()
    expect(downloadMusicXmlClient).toHaveBeenCalledWith(
      '<score-partwise version="3.1"></score-partwise>',
      'song',
    )
  })

  it('downloads MusicXML when the button is clicked', async () => {
    const user = userEvent.setup()

    render(<ExportPanel musicXml={'<score-partwise version="3.1"></score-partwise>'} jobFilename="song.wav" />)

    await user.click(screen.getByRole('button', { name: /musicxml/i }))

    expect(downloadMusicXmlClient).toHaveBeenCalledWith(
      '<score-partwise version="3.1"></score-partwise>',
      'song',
    )
  })
})
