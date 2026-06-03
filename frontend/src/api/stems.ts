// AI-assisted: Milestone 2 stem URL helpers for playback and download.

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

export function getStemStreamUrl(jobId: string, stemName: string): string {
  return `${API_BASE}/api/jobs/${jobId}/stems/${stemName}`
}

export function getStemDownloadUrl(jobId: string, stemName: string): string {
  return `${API_BASE}/api/jobs/${jobId}/stems/${stemName}?download=true`
}
