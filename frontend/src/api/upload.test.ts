import { describe, expect, it } from 'vitest'

import { validateClientWavFile } from './upload'

describe('validateClientWavFile', () => {
  it('accepts a valid wav file', () => {
    const file = new File(['data'], 'song.wav', { type: 'audio/wav' })
    expect(validateClientWavFile(file, 50)).toBeNull()
  })

  it('rejects non-wav extensions', () => {
    const file = new File(['data'], 'song.mp3', { type: 'audio/mpeg' })
    expect(validateClientWavFile(file, 50)).toMatch(/Only \.wav files/)
  })

  it('rejects empty files', () => {
    const file = new File([], 'song.wav', { type: 'audio/wav' })
    expect(validateClientWavFile(file, 50)).toMatch(/empty/)
  })
})
