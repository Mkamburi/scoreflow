import type { JobStatusResponse } from '../types/pipeline'

const PROCESSING_HINTS: Partial<Record<JobStatusResponse['status'], string>> = {
  queued: 'Queued — starting soon…',
  received: 'Received — preparing your upload…',
  separating: 'Separating stems (Demucs) — often about 1–3 minutes for a few-minute song on CPU.',
  transcribing:
    'Transcribing stems (Basic Pitch) — slowest step; can take several minutes per stem on CPU. Stems are already split.',
  notating: 'Building SATB notation from MIDI…',
  processing: 'Processing your upload…',
}

export function processingHintForStatus(
  status: JobStatusResponse['status'] | null | undefined,
): string {
  if (!status) {
    return 'Processing your upload…'
  }
  return PROCESSING_HINTS[status] ?? 'Processing your upload…'
}
