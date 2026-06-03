// AI-assisted: Read-only OSMD score viewer — white stage for visible notation.

import { useEffect, useRef, useState } from 'react'
import { OpenSheetMusicDisplay } from 'opensheetmusicdisplay'

interface ScoreViewerProps {
  musicXml: string | null
  error?: string | null
  embedded?: boolean
}

export function ScoreViewer({ musicXml, error, embedded = false }: ScoreViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [zoom, setZoom] = useState(0.8)
  const [renderError, setRenderError] = useState<string | null>(null)
  const [isRendering, setIsRendering] = useState(false)

  useEffect(() => {
    const container = containerRef.current
    if (!container || !musicXml?.trim()) {
      setRenderError(null)
      setIsRendering(false)
      return
    }

    let cancelled = false
    setIsRendering(true)
    setRenderError(null)

    const renderScore = async () => {
      try {
        container.innerHTML = ''
        const osmd = new OpenSheetMusicDisplay(container, {
          autoResize: true,
          drawTitle: true,
          drawComposer: false,
        })
        await osmd.load(musicXml)
        if (cancelled) {
          return
        }
        osmd.zoom = zoom
        osmd.render()
      } catch (loadError: unknown) {
        console.error('OSMD render failed:', loadError)
        if (!cancelled) {
          setRenderError(
            'Could not draw this score in the browser. Try Download MusicXML and open in MuseScore or Flat.io.',
          )
        }
      } finally {
        if (!cancelled) {
          setIsRendering(false)
        }
      }
    }

    void renderScore()

    return () => {
      cancelled = true
      container.innerHTML = ''
    }
  }, [musicXml, zoom])

  const shellClass = embedded ? 'mt-4 w-full text-left' : 'sf-card mt-6 w-full max-w-4xl p-6 text-left'

  if (error) {
    return (
      <section className={shellClass}>
        <h2 className="sf-heading text-lg text-[var(--color-sf-orange)]">Score unavailable</h2>
        <p className="mt-2 text-sm text-[var(--color-sf-text-muted)]">{error}</p>
      </section>
    )
  }

  return (
    <section className={shellClass}>
      {!embedded && (
        <div className="flex items-center justify-between gap-4">
          <h2 className="sf-heading text-lg">SATB score</h2>
          {musicXml?.trim() && (
            <div className="flex items-center gap-2">
              <button
                type="button"
                aria-label="Zoom out"
                onClick={() => setZoom((value) => Math.max(0.4, Number((value - 0.1).toFixed(1))))}
                className="sf-neu-btn-round h-9 w-9 text-sm"
              >
                −
              </button>
              <span className="sf-mono min-w-16 text-center text-sm text-[var(--color-sf-orange)]">
                {Math.round(zoom * 100)}%
              </span>
              <button
                type="button"
                aria-label="Zoom in"
                onClick={() => setZoom((value) => Math.min(1.5, Number((value + 0.1).toFixed(1))))}
                className="sf-neu-btn-round h-9 w-9 text-sm"
              >
                +
              </button>
            </div>
          )}
        </div>
      )}

      {embedded && musicXml?.trim() && (
        <div className="mb-2 flex items-center justify-end gap-2">
          <button
            type="button"
            aria-label="Zoom out"
            onClick={() => setZoom((value) => Math.max(0.4, Number((value - 0.1).toFixed(1))))}
            className="sf-neu-btn-round h-8 w-8 text-xs"
          >
            −
          </button>
          <span className="sf-mono text-xs text-[var(--color-sf-orange)]">{Math.round(zoom * 100)}%</span>
          <button
            type="button"
            aria-label="Zoom in"
            onClick={() => setZoom((value) => Math.min(1.5, Number((value + 0.1).toFixed(1))))}
            className="sf-neu-btn-round h-8 w-8 text-xs"
          >
            +
          </button>
        </div>
      )}

      {!musicXml?.trim() && !embedded && (
        <p className="sf-text-muted mt-2 text-sm">Your score will appear here once processing completes.</p>
      )}

      {isRendering && <p className="sf-text-muted mt-2 text-sm">Rendering notation…</p>}

      {renderError && (
        <p className="sf-status-error mt-2 rounded-lg px-3 py-2 text-sm">{renderError}</p>
      )}

      <div
        ref={containerRef}
        className={[
          'sf-osmd-viewer sf-card-inner overflow-auto p-2',
          embedded ? 'mt-2 min-h-[320px] max-h-[65vh]' : 'mt-4 min-h-[280px] max-h-[70vh]',
          musicXml?.trim() ? 'block' : 'hidden',
        ].join(' ')}
      />
    </section>
  )
}
