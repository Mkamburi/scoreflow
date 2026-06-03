// AI-assisted: Flat.io embed editor — neumorphic raised container.

import Embed from 'flat-embed'
import { useEffect, useRef, useState } from 'react'

const SYNC_DEBOUNCE_MS = 750

function getFlatAppId(): string {
  return import.meta.env.VITE_FLAT_APP_ID?.trim() ?? ''
}

export function isFlatEditorConfigured(): boolean {
  return getFlatAppId().length > 0
}

interface ScoreEditorProps {
  musicXml: string
  reloadKey: number
  onScoreChange: (musicXml: string) => void
  onEmbedReady?: (embed: Embed) => void
  onLoadError?: () => void
}

export function ScoreEditor({
  musicXml,
  reloadKey,
  onScoreChange,
  onEmbedReady,
  onLoadError,
}: ScoreEditorProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const embedRef = useRef<Embed | null>(null)
  const musicXmlRef = useRef(musicXml)
  const skipSyncRef = useRef(false)
  const syncTimerRef = useRef<number | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  musicXmlRef.current = musicXml

  useEffect(() => {
    const container = containerRef.current
    if (!container || !isFlatEditorConfigured()) {
      return
    }

    const embed = new Embed(container, {
      width: '100%',
      height: '640px',
      embedParams: {
        appId: getFlatAppId(),
        mode: 'edit',
        layout: 'responsive',
        controlsPosition: 'bottom',
        branding: true,
        themePrimary: '#e85d04',
      },
    })

    embedRef.current = embed
    onEmbedReady?.(embed)

    const scheduleSync = () => {
      if (skipSyncRef.current || syncTimerRef.current !== null) {
        return
      }

      syncTimerRef.current = window.setTimeout(() => {
        syncTimerRef.current = null
        void embed
          .getMusicXML()
          .then((xml) => {
            if (typeof xml === 'string' && xml.trim()) {
              onScoreChange(xml)
            }
          })
          .catch((error: unknown) => {
            console.error('Failed to sync MusicXML from Flat embed:', error)
          })
      }, SYNC_DEBOUNCE_MS)
    }

    // Sync edits after selection changes — not on noteDetails (that refires on every
    // note click and used to reload the iframe via parent state, breaking note preview audio).
    const handleEditSync = () => {
      scheduleSync()
    }

    embed.on('rangeSelection', handleEditSync)

    return () => {
      embed.off('rangeSelection', handleEditSync)
      if (syncTimerRef.current !== null) {
        window.clearTimeout(syncTimerRef.current)
      }
    }
  }, [onEmbedReady, onScoreChange])

  useEffect(() => {
    const embed = embedRef.current
    const xml = musicXmlRef.current
    if (!embed || !xml.trim()) {
      return
    }

    skipSyncRef.current = true
    setIsLoading(true)
    setLoadError(null)

    const loadScore = async () => {
      try {
        await embed.ready()
        await embed.loadMusicXML(xml)
      } catch (error: unknown) {
        console.error('Flat embed failed to load MusicXML:', error)
        setLoadError('Flat.io could not open this score. Use the notation preview above.')
        onLoadError?.()
      } finally {
        skipSyncRef.current = false
        setIsLoading(false)
      }
    }

    void loadScore()
    // Only reload the iframe when reloadKey changes (new upload, undo/redo) — not on every edit sync.
  }, [reloadKey, onLoadError])

  if (!isFlatEditorConfigured()) {
    return (
      <div className="sf-status-warning rounded-xl px-4 py-3 text-sm">
        <p className="font-semibold text-[var(--color-sf-orange)]">Flat.io editor not configured</p>
        <p className="sf-text-muted mt-1">
          Add <code className="sf-mono text-[var(--color-sf-orange)]">VITE_FLAT_APP_ID</code> to{' '}
          <code className="sf-mono text-[var(--color-sf-orange)]">frontend/.env</code> (create a free app at{' '}
          <a className="sf-link text-[var(--color-sf-orange)]" href="https://flat.io/developers/apps" target="_blank" rel="noreferrer">
            flat.io/developers/apps
          </a>
          ).
        </p>
      </div>
    )
  }

  return (
    <div>
      {isLoading && (
        <p className="sf-text-muted mb-3 text-sm">Loading editor… click notes to select and edit.</p>
      )}
      {loadError && <p className="sf-status-error mb-3 rounded-lg px-3 py-2 text-sm">{loadError}</p>}
      <div
        ref={containerRef}
        className="sf-card-inner min-h-[640px] overflow-hidden"
        data-testid="flat-editor-container"
      />
    </div>
  )
}
