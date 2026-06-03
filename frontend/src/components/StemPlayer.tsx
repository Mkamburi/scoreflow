// AI-assisted: Milestone 2 stem playback — listen to and download Demucs stems in the browser.

import type { JobStatusResponse } from '../types/pipeline'
import { getStemDownloadUrl, getStemStreamUrl } from '../api/stems'

interface StemPlayerProps {
  jobStatus: JobStatusResponse
}

const STEM_ORDER = ['vocals', 'drums', 'bass', 'other'] as const

const STEM_LABELS: Record<(typeof STEM_ORDER)[number], string> = {
  vocals: 'Vocals',
  drums: 'Drums',
  bass: 'Bass',
  other: 'Other',
}

export function StemPlayer({ jobStatus }: StemPlayerProps) {
  if (!jobStatus.demucs_stems || jobStatus.status !== 'completed') {
    return null
  }

  return (
    <section className="mt-6 w-full max-w-2xl rounded-2xl border border-slate-200 bg-white p-6 text-left shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">Listen to separated stems</h2>
      <p className="mt-1 text-sm text-slate-600">
        Preview each Demucs stem or download the WAV files.
      </p>

      <ul className="mt-5 space-y-5">
        {STEM_ORDER.filter((stem) => jobStatus.demucs_stems?.[stem]).map((stem) => (
          <li key={stem} className="rounded-xl border border-slate-200 bg-slate-50 p-4">
            <div className="mb-3 flex items-center justify-between gap-3">
              <h3 className="font-medium text-slate-900">{STEM_LABELS[stem]}</h3>
              <a
                href={getStemDownloadUrl(jobStatus.job_id, stem)}
                download={`${stem}.wav`}
                className="text-sm font-medium text-violet-600 hover:text-violet-700"
              >
                Download WAV
              </a>
            </div>
            <audio controls className="w-full" src={getStemStreamUrl(jobStatus.job_id, stem)}>
              Your browser does not support audio playback.
            </audio>
          </li>
        ))}
      </ul>
    </section>
  )
}
