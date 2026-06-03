// AI-assisted: Milestone 3.5 score state — MusicXML history with 20-step undo/redo.

import { useCallback, useRef, useState } from 'react'

import { SCORE_HISTORY_LIMIT, type ScoreHistoryState } from '../types/score'

export function useScore(): ScoreHistoryState & {
  resetScore: (musicXml: string) => void
  recordEdit: (musicXml: string) => void
  undo: () => string | null
  redo: () => string | null
  clearScore: () => void
} {
  const [musicXml, setMusicXml] = useState<string | null>(null)
  const [canUndo, setCanUndo] = useState(false)
  const [canRedo, setCanRedo] = useState(false)
  const musicXmlRef = useRef<string | null>(null)
  const historyRef = useRef<string[]>([])
  const futureRef = useRef<string[]>([])

  const updateHistoryFlags = useCallback(() => {
    setCanUndo(historyRef.current.length > 0)
    setCanRedo(futureRef.current.length > 0)
  }, [])

  const resetScore = useCallback(
    (nextMusicXml: string) => {
      historyRef.current = []
      futureRef.current = []
      musicXmlRef.current = nextMusicXml
      setMusicXml(nextMusicXml)
      updateHistoryFlags()
    },
    [updateHistoryFlags],
  )

  const clearScore = useCallback(() => {
    historyRef.current = []
    futureRef.current = []
    musicXmlRef.current = null
    setMusicXml(null)
    updateHistoryFlags()
  }, [updateHistoryFlags])

  const recordEdit = useCallback(
    (nextMusicXml: string) => {
      const current = musicXmlRef.current
      if (!current || current === nextMusicXml) {
        return
      }

      historyRef.current = [...historyRef.current, current].slice(-SCORE_HISTORY_LIMIT)
      futureRef.current = []
      musicXmlRef.current = nextMusicXml
      setMusicXml(nextMusicXml)
      updateHistoryFlags()
    },
    [updateHistoryFlags],
  )

  const undo = useCallback((): string | null => {
    const previous = historyRef.current.pop()
    if (!previous) {
      return null
    }

    const current = musicXmlRef.current
    if (current) {
      futureRef.current = [current, ...futureRef.current].slice(0, SCORE_HISTORY_LIMIT)
    }

    musicXmlRef.current = previous
    setMusicXml(previous)
    updateHistoryFlags()
    return previous
  }, [updateHistoryFlags])

  const redo = useCallback((): string | null => {
    const next = futureRef.current.shift()
    if (!next) {
      return null
    }

    const current = musicXmlRef.current
    if (current) {
      historyRef.current = [...historyRef.current, current].slice(-SCORE_HISTORY_LIMIT)
    }

    musicXmlRef.current = next
    setMusicXml(next)
    updateHistoryFlags()
    return next
  }, [updateHistoryFlags])

  return {
    musicXml,
    canUndo,
    canRedo,
    resetScore,
    recordEdit,
    undo,
    redo,
    clearScore,
  }
}
