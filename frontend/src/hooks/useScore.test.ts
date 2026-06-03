import { act, renderHook } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { SCORE_HISTORY_LIMIT } from '../types/score'
import { useScore } from './useScore'

const ORIGINAL_XML = '<score-partwise version="3.1"><part-list></part-list></score-partwise>'
const EDIT_ONE = '<score-partwise version="3.1"><part-list><edit>1</edit></part-list></score-partwise>'
const EDIT_TWO = '<score-partwise version="3.1"><part-list><edit>2</edit></part-list></score-partwise>'
const EDIT_THREE = '<score-partwise version="3.1"><part-list><edit>3</edit></part-list></score-partwise>'

describe('useScore', () => {
  it('tracks edits and restores the original MusicXML after three undos', () => {
    const { result } = renderHook(() => useScore())

    act(() => {
      result.current.resetScore(ORIGINAL_XML)
      result.current.recordEdit(EDIT_ONE)
      result.current.recordEdit(EDIT_TWO)
      result.current.recordEdit(EDIT_THREE)
    })

    expect(result.current.musicXml).toBe(EDIT_THREE)
    expect(result.current.canUndo).toBe(true)

    act(() => {
      result.current.undo()
      result.current.undo()
      result.current.undo()
    })

    expect(result.current.musicXml).toBe(ORIGINAL_XML)
    expect(result.current.canRedo).toBe(true)
  })

  it('redoes a reverted edit', () => {
    const { result } = renderHook(() => useScore())

    act(() => {
      result.current.resetScore(ORIGINAL_XML)
      result.current.recordEdit(EDIT_ONE)
      result.current.undo()
    })

    expect(result.current.musicXml).toBe(ORIGINAL_XML)

    act(() => {
      result.current.redo()
    })

    expect(result.current.musicXml).toBe(EDIT_ONE)
  })

  it('caps undo history at the configured limit', () => {
    const { result } = renderHook(() => useScore())

    act(() => {
      result.current.resetScore(ORIGINAL_XML)
      for (let index = 0; index < SCORE_HISTORY_LIMIT + 5; index += 1) {
        result.current.recordEdit(`${EDIT_ONE}-${index}`)
      }
    })

    for (let index = 0; index < SCORE_HISTORY_LIMIT; index += 1) {
      act(() => {
        result.current.undo()
      })
    }

    expect(result.current.musicXml).not.toBe(ORIGINAL_XML)
    expect(result.current.canUndo).toBe(false)
  })
})
