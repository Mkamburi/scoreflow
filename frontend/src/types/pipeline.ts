// AI-assisted: Milestone 1 shared pipeline types for upload + job polling.

export type JobStatus =
  | 'queued'
  | 'received'
  | 'separating'
  | 'transcribing'
  | 'notating'
  | 'processing'
  | 'completed'
  | 'failed'

export interface UploadResponse {
  job_id: string
  status: JobStatus
  message: string
}

export interface JobStatusResponse {
  job_id: string
  status: JobStatus
  original_filename: string
  size_bytes: number
  created_at: string
  updated_at: string
  error?: string | null
  stems_dir?: string | null
  demucs_stems?: Record<string, string> | null
  satb_stems?: Record<string, string | null> | null
  warnings?: string[]
  has_score?: boolean
}

export interface UploadProgress {
  loaded: number
  total: number
  percent: number
}

export type UploadState =
  | { phase: 'idle' }
  | { phase: 'uploading'; progress: UploadProgress; fileName: string }
  | { phase: 'success'; jobId: string; message: string }
  | { phase: 'error'; message: string }
