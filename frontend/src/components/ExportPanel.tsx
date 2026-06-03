// AI-assisted: Milestone 4 export panel — neumorphic action card.

import type Embed from 'flat-embed'
import { useCallback, useState } from 'react'

import { downloadBlob, downloadMusicXmlClient, exportScore } from '../api/export'

interface ExportPanelProps {
  musicXml: string
  jobFilename?: string | null
  flatEmbed?: Embed | null
}

const FLAT_SYNC_TIMEOUT_MS = 4000

export function ExportPanel({ musicXml, jobFilename, flatEmbed }: ExportPanelProps) {
  const [status, setStatus] = useState<string | null>(null)
  const [isExporting, setIsExporting] = useState(false)

  const baseName = (jobFilename ?? 'scoreflow-score').replace(/\.wav$/i, '')

  const syncFromEditor = useCallback(async (): Promise<string> => {
    if (!flatEmbed || !musicXml.trim()) {
      return musicXml
    }

    try {
      const latest = await Promise.race([
        flatEmbed.getMusicXML(),
        new Promise<never>((_, reject) => {
          window.setTimeout(() => reject(new Error('Flat editor sync timed out.')), FLAT_SYNC_TIMEOUT_MS)
        }),
      ])
      return typeof latest === 'string' && latest.trim() ? latest : musicXml
    } catch {
      return musicXml
    }
  }, [flatEmbed, musicXml])

  const runExport = useCallback(
    async (format: 'musicxml' | 'midi' | 'pdf') => {
      setIsExporting(true)
      setStatus(null)

      try {
        const xmlForExport =
          format === 'musicxml' ? musicXml : await syncFromEditor()

        if (!xmlForExport.trim()) {
          throw new Error('No score to export yet. Wait for notation to finish loading.')
        }

        if (format === 'musicxml') {
          downloadMusicXmlClient(xmlForExport, baseName)
          setStatus('MusicXML downloaded.')
          return
        }

        const blob = await exportScore(format, { musicXml: xmlForExport, filename: baseName })
        const extension = format === 'midi' ? 'mid' : 'pdf'
        downloadBlob(blob, `${baseName}.${extension}`)
        setStatus(`${extension.toUpperCase()} downloaded.`)
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Export failed.'
        setStatus(message)
      } finally {
        setIsExporting(false)
      }
    },
    [baseName, musicXml, syncFromEditor],
  )

  const handlePrint = useCallback(() => {
    window.print()
    setStatus('Use your browser print dialog to save as PDF.')
  }, [])

  return (
    <section className="sf-card-inner mt-4 p-4">
      <h3 className="sf-label">Export score</h3>
      <p className="sf-text-muted mt-1 text-xs">
        Downloads use your latest edits from the editor when Flat.io is active.
      </p>

      <div className="mt-3 flex flex-wrap gap-2">
        <button
          type="button"
          disabled={isExporting}
          onClick={() => void runExport('musicxml')}
          className="sf-btn-ghost px-3 py-1.5 text-sm disabled:opacity-40"
        >
          MusicXML
        </button>
        <button
          type="button"
          disabled={isExporting}
          onClick={() => void runExport('midi')}
          className="sf-btn-ghost px-3 py-1.5 text-sm disabled:opacity-40"
        >
          MIDI
        </button>
        <button
          type="button"
          disabled={isExporting}
          onClick={() => void runExport('pdf')}
          className="sf-btn-ghost px-3 py-1.5 text-sm disabled:opacity-40"
        >
          PDF (server)
        </button>
        <button type="button" onClick={handlePrint} className="sf-btn-ghost px-3 py-1.5 text-sm">
          Print to PDF
        </button>
      </div>

      {status && <p className="sf-mono mt-2 text-xs text-[var(--color-sf-orange)]">{status}</p>}
    </section>
  )
}
