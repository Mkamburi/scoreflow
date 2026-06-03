// AI-assisted: Milestone 1 drag-and-drop WAV upload — neumorphic inset drop zone.

import { useRef, useState, type ChangeEvent, type DragEvent } from 'react'

import type { UploadState } from '../types/pipeline'

interface UploadZoneProps {
  uploadState: UploadState
  onFileSelected: (file: File) => void
  onReset: () => void
}

export function UploadZone({ uploadState, onFileSelected, onReset }: UploadZoneProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [isDragging, setIsDragging] = useState(false)

  const handleFiles = (files: FileList | null) => {
    const file = files?.[0]
    if (file) {
      onFileSelected(file)
    }
  }

  const onInputChange = (event: ChangeEvent<HTMLInputElement>) => {
    handleFiles(event.target.files)
    event.target.value = ''
  }

  const onDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setIsDragging(false)
    handleFiles(event.dataTransfer.files)
  }

  const isUploading = uploadState.phase === 'uploading'

  return (
    <section className="sf-card w-full max-w-2xl p-8">
      <div
        role="button"
        tabIndex={0}
        aria-label="Upload WAV file"
        onClick={() => !isUploading && inputRef.current?.click()}
        onKeyDown={(event) => {
          if ((event.key === 'Enter' || event.key === ' ') && !isUploading) {
            event.preventDefault()
            inputRef.current?.click()
          }
        }}
        onDragOver={(event) => {
          event.preventDefault()
          setIsDragging(true)
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={onDrop}
        className={[
          'sf-dropzone flex min-h-48 cursor-pointer flex-col items-center justify-center px-6 py-10 text-center transition',
          isDragging ? 'sf-dropzone--drag' : '',
          isUploading ? 'pointer-events-none opacity-70' : '',
        ].join(' ')}
      >
        <p className="text-lg font-semibold text-[var(--color-sf-text)]">Drop a WAV file here</p>
        <p className="sf-text-muted mt-2 text-sm">or click to browse · max 50 MB</p>
        <input
          ref={inputRef}
          type="file"
          accept=".wav,audio/wav,audio/x-wav"
          className="hidden"
          onChange={onInputChange}
          disabled={isUploading}
        />
      </div>

      {uploadState.phase === 'uploading' && (
        <div className="mt-6">
          <div className="mb-2 flex items-center justify-between text-sm text-[var(--color-sf-orange)]">
            <span>Uploading {uploadState.fileName}</span>
            <span className="sf-mono">{uploadState.progress.percent}%</span>
          </div>
          <div className="sf-progress-track h-2 overflow-hidden">
            <div
              className="sf-progress-fill h-full transition-all"
              style={{ width: `${uploadState.progress.percent}%` }}
            />
          </div>
        </div>
      )}

      {uploadState.phase === 'success' && (
        <div className="sf-status-success mt-6 rounded-lg px-4 py-3 text-sm">
          Upload complete. Job ID:{' '}
          <code className="sf-mono text-[var(--color-sf-orange)]">{uploadState.jobId}</code>
        </div>
      )}

      {uploadState.phase === 'error' && (
        <div className="sf-status-error mt-6 rounded-lg px-4 py-3 text-sm">{uploadState.message}</div>
      )}

      {uploadState.phase !== 'idle' && (
        <button
          type="button"
          onClick={onReset}
          disabled={isUploading}
          className="sf-btn-ghost mt-4 px-4 py-2 text-sm disabled:opacity-40"
        >
          Upload another file
        </button>
      )}
    </section>
  )
}
