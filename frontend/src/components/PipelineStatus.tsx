// AI-assisted: Pipeline status panel — neumorphic project card.

import type { JobStatusResponse } from '../types/pipeline'

interface PipelineStatusProps {
  jobStatus: JobStatusResponse | null
}

const STATUS_LABELS: Record<JobStatusResponse['status'], string> = {
  queued: 'Queued',
  received: 'Received',
  separating: 'Separating stems',
  transcribing: 'Transcribing',
  notating: 'Building score',
  processing: 'Processing',
  completed: 'Completed',
  failed: 'Failed',
}

export function PipelineStatus({ jobStatus }: PipelineStatusProps) {
  if (!jobStatus) {
    return null
  }

  return (
    <section className="sf-card mt-6 w-full max-w-2xl p-6 text-left">
      <h2 className="sf-heading text-lg">Pipeline status</h2>
      <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
        <div>
          <dt className="sf-label">Job ID</dt>
          <dd className="sf-mono mt-1 break-all text-[var(--color-sf-text)]">{jobStatus.job_id}</dd>
        </div>
        <div>
          <dt className="sf-label">Status</dt>
          <dd className="mt-1 font-semibold text-[var(--color-sf-orange)]">
            {STATUS_LABELS[jobStatus.status]}
          </dd>
          {jobStatus.status === 'separating' && (
            <p className="sf-text-muted mt-1 text-xs">Running Demucs stem separation (about 1–3 min).</p>
          )}
          {jobStatus.status === 'transcribing' && jobStatus.demucs_stems && (
            <p className="sf-text-muted mt-1 text-xs">
              Stem separation is done. Basic Pitch is building MIDI for the score.
            </p>
          )}
        </div>
        <div>
          <dt className="sf-label">File</dt>
          <dd className="sf-text-muted mt-1">{jobStatus.original_filename}</dd>
        </div>
        <div>
          <dt className="sf-label">Size</dt>
          <dd className="sf-mono mt-1 text-[var(--color-sf-text)]">
            {(jobStatus.size_bytes / (1024 * 1024)).toFixed(2)} MB
          </dd>
        </div>
      </dl>

      {jobStatus.satb_stems && (
        <div className="mt-4">
          <h3 className="sf-label">SATB stem mapping</h3>
          <ul className="mt-2 space-y-1 text-sm">
            {Object.entries(jobStatus.satb_stems).map(([role, path]) => (
              <li key={role}>
                <span className="font-semibold capitalize text-[var(--color-sf-orange)]">{role}</span>
                <span className="sf-text-muted">: </span>
                {path ? <span className="sf-mono text-xs">{path}</span> : <span className="sf-text-muted">omitted</span>}
              </li>
            ))}
          </ul>
        </div>
      )}

      {jobStatus.warnings?.map((warning) => (
        <p key={warning} className="sf-status-warning mt-4 rounded-lg px-3 py-2 text-sm">
          {warning}
        </p>
      ))}

      {jobStatus.error && (
        <p className="sf-status-error mt-4 rounded-lg px-3 py-2 text-sm">{jobStatus.error}</p>
      )}
    </section>
  )
}
