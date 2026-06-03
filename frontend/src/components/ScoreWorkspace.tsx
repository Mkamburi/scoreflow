// AI-assisted: Score workspace — OSMD preview always shown; Flat editor optional below.

import type Embed from 'flat-embed'
import { useCallback, useEffect, useMemo, useState } from 'react'

import { useScore } from '../hooks/useScore'
import { CompletionPanel } from './CompletionPanel'
import { EditorToolbar } from './EditorToolbar'
import { ExportPanel } from './ExportPanel'
import { ScoreEditor, isFlatEditorConfigured } from './ScoreEditor'
import { ScoreViewer } from './ScoreViewer'
import { processingHintForStatus } from '../lib/pipelineMessages'
import type { JobStatusResponse } from '../types/pipeline'

interface ScoreWorkspaceProps {
  pipelineMusicXml: string | null
  scoreError?: string | null
  isPipelineComplete: boolean
  isProcessing: boolean
  isFetchingScore: boolean
  pipelineStatus?: JobStatusResponse['status'] | null
  jobFilename?: string | null
  onEmbedReady?: (embed: Embed) => void
}

export function ScoreWorkspace({
  pipelineMusicXml,
  scoreError,
  isPipelineComplete,
  isProcessing,
  isFetchingScore,
  pipelineStatus,
  jobFilename,
  onEmbedReady,
}: ScoreWorkspaceProps) {
  const { musicXml, canUndo, canRedo, resetScore, recordEdit, undo, redo, clearScore } = useScore()
  const [reloadKey, setReloadKey] = useState(0)
  const [flatEmbed, setFlatEmbed] = useState<Embed | null>(null)
  const [flatLoadFailed, setFlatLoadFailed] = useState(false)

  const activeMusicXml = useMemo(() => {
    if (musicXml?.trim()) {
      return musicXml
    }
    if (pipelineMusicXml?.trim()) {
      return pipelineMusicXml
    }
    return null
  }, [musicXml, pipelineMusicXml])

  useEffect(() => {
    if (pipelineMusicXml?.trim()) {
      resetScore(pipelineMusicXml)
      setReloadKey((value) => value + 1)
      setFlatLoadFailed(false)
    } else if (!isPipelineComplete && !isProcessing) {
      clearScore()
      setFlatEmbed(null)
      setFlatLoadFailed(false)
    }
  }, [clearScore, isPipelineComplete, isProcessing, pipelineMusicXml, resetScore])

  const handleEmbedReady = useCallback(
    (embed: Embed) => {
      setFlatEmbed(embed)
      onEmbedReady?.(embed)
    },
    [onEmbedReady],
  )

  const handleUndo = useCallback(() => {
    if (undo()) {
      setReloadKey((value) => value + 1)
    }
  }, [undo])

  const handleRedo = useCallback(() => {
    if (redo()) {
      setReloadKey((value) => value + 1)
    }
  }, [redo])

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      const isMeta = event.metaKey || event.ctrlKey
      if (!isMeta || event.key.toLowerCase() !== 'z') {
        return
      }
      event.preventDefault()
      if (event.shiftKey) {
        handleRedo()
      } else {
        handleUndo()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [handleRedo, handleUndo])

  const downloadMusicXml = () => {
    if (!activeMusicXml) {
      return
    }
    const blob = new Blob([activeMusicXml], { type: 'application/vnd.recordare.musicxml+xml' })
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = `${jobFilename?.replace(/\.[^.]+$/, '') ?? 'scoreflow'}-score.musicxml`
    anchor.click()
    URL.revokeObjectURL(url)
  }

  const previewHint = useMemo(() => {
    if (scoreError) {
      return scoreError
    }
    if (isFetchingScore) {
      return 'Downloading your score from the server…'
    }
    if (isProcessing) {
      return processingHintForStatus(pipelineStatus)
    }
    if (activeMusicXml) {
      return 'Scroll in the white box below to view all parts.'
    }
    if (isPipelineComplete) {
      return 'Processing finished but no score loaded. Check Pipeline status for errors.'
    }
    return 'Upload a WAV file to generate your SATB score.'
  }, [activeMusicXml, isFetchingScore, isPipelineComplete, isProcessing, pipelineStatus, scoreError])

  const editorConfigured = isFlatEditorConfigured() && !flatLoadFailed && Boolean(activeMusicXml)

  return (
    <section className="sf-card mt-6 w-full max-w-4xl p-6 text-left">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="sf-heading text-lg">SATB score</h2>
        {activeMusicXml && (
          <button type="button" className="sf-neu-btn px-4 py-2 text-sm" onClick={downloadMusicXml}>
            Download MusicXML
          </button>
        )}
      </div>

      <div className="mt-4 rounded-xl border-2 border-[var(--color-sf-orange)]/35 px-4 py-3">
        <p className="sf-label">Notation preview</p>
        <p className={`mt-2 text-sm ${scoreError ? 'text-[var(--color-sf-orange)]' : 'sf-text-muted'}`}>
          {previewHint}
        </p>
      </div>

      {activeMusicXml ? (
        <>
          <EditorToolbar
            canUndo={canUndo}
            canRedo={canRedo}
            onUndo={handleUndo}
            onRedo={handleRedo}
            isEditorActive={editorConfigured}
          />
          <ScoreViewer musicXml={activeMusicXml} embedded />
        </>
      ) : (
        <div className="sf-osmd-viewer sf-card-inner mt-4 flex min-h-[220px] items-center justify-center p-6">
          <p className="sf-text-muted text-center text-sm">
            {isProcessing || isFetchingScore
              ? 'Your notation will appear in this white area when ready…'
              : 'No score loaded yet.'}
          </p>
        </div>
      )}

      {activeMusicXml && isFlatEditorConfigured() && (
        <div className="mt-6">
          <p className="sf-label mb-2">Edit in Flat.io (optional)</p>
          <p className="sf-text-muted mb-2 text-xs">
            Click a note to hear a short preview. If audio spins, wait for the score to finish loading, or
            use the white notation preview above. Stop a ringing note with the center pause button on the
            bottom transport bar (or Flat&apos;s stop control).
          </p>
          {flatLoadFailed ? (
            <p className="sf-status-error rounded-lg px-3 py-2 text-sm">
              Flat.io could not open this file. Use the notation preview above or Download MusicXML.
            </p>
          ) : (
            <ScoreEditor
              musicXml={activeMusicXml}
              reloadKey={reloadKey}
              onScoreChange={recordEdit}
              onEmbedReady={handleEmbedReady}
              onLoadError={() => setFlatLoadFailed(true)}
            />
          )}
        </div>
      )}

      {activeMusicXml && (
        <>
          <ExportPanel musicXml={activeMusicXml} jobFilename={jobFilename} flatEmbed={flatEmbed} />
          {editorConfigured && (
            <CompletionPanel
              musicXml={activeMusicXml}
              flatEmbed={flatEmbed}
              onScoreUpdated={(xml) => {
                recordEdit(xml)
                setReloadKey((value) => value + 1)
              }}
            />
          )}
        </>
      )}
    </section>
  )
}
