// AI-assisted: Milestone 5 AI completion — neumorphic optional panel.

import type Embed from 'flat-embed'
import { useCallback, useEffect, useState } from 'react'

import { fetchCompletionStatus, suggestHarmony } from '../api/completion'

interface CompletionPanelProps {
  musicXml: string
  flatEmbed?: Embed | null
  onScoreUpdated: (musicXml: string) => void
}

export function CompletionPanel({ musicXml, flatEmbed, onScoreUpdated }: CompletionPanelProps) {
  const [enabled, setEnabled] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [message, setMessage] = useState<string | null>(null)

  useEffect(() => {
    void fetchCompletionStatus().then(setEnabled)
  }, [])

  const syncFromEditor = useCallback(async (): Promise<string> => {
    if (!flatEmbed) {
      return musicXml
    }

    const latest = await flatEmbed.getMusicXML()
    return typeof latest === 'string' ? latest : musicXml
  }, [flatEmbed, musicXml])

  const handleSuggest = useCallback(async () => {
    setIsLoading(true)
    setMessage(null)

    try {
      const latestXml = await syncFromEditor()
      const result = await suggestHarmony({ musicXml: latestXml, targetPart: 'Bass' })

      if (!result.success || !result.music_xml) {
        throw new Error(result.error ?? 'No harmony was generated.')
      }

      onScoreUpdated(result.music_xml)
      setMessage(
        result.warnings.length > 0
          ? `Harmony added. ${result.warnings[0]}`
          : 'Harmony suggestions merged into the Bass part.',
      )
    } catch (error) {
      const text = error instanceof Error ? error.message : 'Completion failed.'
      setMessage(text)
    } finally {
      setIsLoading(false)
    }
  }, [onScoreUpdated, syncFromEditor])

  if (!enabled) {
    return (
      <section className="sf-card-inner mt-4 p-4 text-left">
        <h3 className="sf-text-muted text-sm font-semibold">AI completion (optional)</h3>
        <p className="sf-text-muted mt-1 text-xs">
          Disabled on the server. Set ENABLE_AI_COMPLETION=true in backend/.env to enable bass
          harmony suggestions.
        </p>
      </section>
    )
  }

  return (
    <section className="sf-card-inner mt-4 p-4 text-left">
      <h3 className="sf-label">AI completion</h3>
      <p className="sf-text-muted mt-1 text-xs">
        Suggest simple bass harmony under the soprano melody. Review edits before exporting.
      </p>

      <button
        type="button"
        disabled={isLoading}
        onClick={() => void handleSuggest()}
        className="sf-btn-primary mt-3 px-4 py-1.5 text-sm disabled:opacity-40"
      >
        {isLoading ? 'Generating…' : 'Suggest bass harmony'}
      </button>

      {message && <p className="sf-mono mt-2 text-xs text-[var(--color-sf-orange)]">{message}</p>}
    </section>
  )
}
