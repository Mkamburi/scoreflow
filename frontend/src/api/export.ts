// AI-assisted: Milestone 4 export API client.

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

export type ExportFormat = 'musicxml' | 'midi' | 'pdf'

export interface ExportPayload {
  musicXml: string
  filename?: string
}

function parseErrorDetail(payload: unknown): string {
  if (!payload || typeof payload !== 'object') {
    return 'Export failed.'
  }

  const detail = (payload as { detail?: unknown }).detail
  if (typeof detail === 'string') {
    return detail
  }

  if (detail && typeof detail === 'object' && 'detail' in detail) {
    const nested = detail as { detail?: string; fallback?: string }
    return [nested.detail, nested.fallback].filter(Boolean).join(' ')
  }

  return 'Export failed.'
}

export async function exportScore(format: ExportFormat, payload: ExportPayload): Promise<Blob> {
  const response = await fetch(`${API_BASE}/api/export/${format}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      music_xml: payload.musicXml,
      filename: payload.filename ?? 'scoreflow-score',
    }),
  })

  if (!response.ok) {
    const errorPayload = (await response.json().catch(() => null)) as unknown
    throw new Error(parseErrorDetail(errorPayload))
  }

  return response.blob()
}

export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.rel = 'noopener'
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(url)
}

export function downloadMusicXmlClient(musicXml: string, filename: string): void {
  const blob = new Blob([musicXml], { type: 'application/vnd.recordare.musicxml+xml' })
  downloadBlob(blob, filename.endsWith('.musicxml') ? filename : `${filename}.musicxml`)
}
