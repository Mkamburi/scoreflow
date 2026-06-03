// AI-assisted: Milestone 1 upload client with XMLHttpRequest progress events.

import type { JobStatusResponse, UploadProgress, UploadResponse } from '../types/pipeline'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

export class UploadError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'UploadError'
  }
}

export async function uploadWavFile(
  file: File,
  onProgress?: (progress: UploadProgress) => void,
): Promise<UploadResponse> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    xhr.open('POST', `${API_BASE}/api/upload`)
    xhr.responseType = 'json'

    xhr.upload.onprogress = (event) => {
      if (!event.lengthComputable || !onProgress) {
        return
      }

      onProgress({
        loaded: event.loaded,
        total: event.total,
        percent: Math.round((event.loaded / event.total) * 100),
      })
    }

    xhr.onload = () => {
      const payload = xhr.response as UploadResponse | { detail?: string }

      if (xhr.status >= 200 && xhr.status < 300 && 'job_id' in payload) {
        resolve(payload)
        return
      }

      const detail =
        typeof payload === 'object' && payload && 'detail' in payload
          ? String(payload.detail)
          : 'Upload failed.'
      reject(new UploadError(detail))
    }

    xhr.onerror = () => reject(new UploadError('Network error during upload.'))

    const formData = new FormData()
    formData.append('file', file)
    xhr.send(formData)
  })
}

export async function fetchJobStatus(jobId: string): Promise<JobStatusResponse> {
  const response = await fetch(`${API_BASE}/api/jobs/${jobId}`)

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null
    throw new UploadError(payload?.detail ?? 'Could not fetch job status.')
  }

  return response.json() as Promise<JobStatusResponse>
}

export function validateClientWavFile(
  file: File,
  maxSizeMb = Number(import.meta.env.VITE_MAX_UPLOAD_SIZE_MB ?? 50),
): string | null {
  const lowerName = file.name.toLowerCase()
  if (!lowerName.endsWith('.wav')) {
    return 'Only .wav files are supported.'
  }

  const allowedTypes = ['audio/wav', 'audio/x-wav', 'audio/wave', 'audio/vnd.wave', '']
  if (file.type && !allowedTypes.includes(file.type)) {
    return `Unsupported file type: ${file.type}`
  }

  const maxBytes = maxSizeMb * 1024 * 1024
  if (file.size > maxBytes) {
    return `File exceeds the ${maxSizeMb} MB limit.`
  }

  if (file.size === 0) {
    return 'File is empty.'
  }

  return null
}
