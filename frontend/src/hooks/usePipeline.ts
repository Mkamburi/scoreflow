// AI-assisted: Milestone 3 pipeline hook — upload, job polling, and score fetch.

import { useCallback, useEffect, useRef, useState } from 'react'

import { fetchJobScore } from '../api/score'
import { fetchJobStatus, uploadWavFile, validateClientWavFile } from '../api/upload'
import type { JobStatusResponse, UploadState } from '../types/pipeline'

const POLL_INTERVAL_MS = 1500

const PROCESSING_STATUSES = new Set([
  'queued',
  'received',
  'separating',
  'transcribing',
  'notating',
  'processing',
])

export function usePipeline() {
  const [uploadState, setUploadState] = useState<UploadState>({ phase: 'idle' })
  const [jobStatus, setJobStatus] = useState<JobStatusResponse | null>(null)
  const [musicXml, setMusicXml] = useState<string | null>(null)
  const [scoreError, setScoreError] = useState<string | null>(null)
  const [isFetchingScore, setIsFetchingScore] = useState(false)
  const pollTimerRef = useRef<number | null>(null)

  const clearPollTimer = useCallback(() => {
    if (pollTimerRef.current !== null) {
      window.clearInterval(pollTimerRef.current)
      pollTimerRef.current = null
    }
  }, [])

  const loadScore = useCallback(async (jobId: string, status: JobStatusResponse) => {
    setIsFetchingScore(true)
    try {
      const score = await fetchJobScore(jobId)
      setMusicXml(score)
      setScoreError(null)
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Could not fetch score.'
      setMusicXml(null)
      setScoreError(status.error ?? message)
    } finally {
      setIsFetchingScore(false)
    }
  }, [])

  const pollJobStatus = useCallback(
    async (jobId: string) => {
      try {
        const status = await fetchJobStatus(jobId)
        setJobStatus(status)

        if (status.status === 'failed') {
          clearPollTimer()
          setMusicXml(null)
          setScoreError(status.error ?? 'Pipeline failed.')
          setUploadState({
            phase: 'error',
            message: status.error ?? 'Pipeline failed.',
          })
          return
        }

        if (status.status === 'completed') {
          clearPollTimer()
          if (status.has_score) {
            await loadScore(jobId, status)
          } else {
            setMusicXml(null)
            setScoreError(
              status.error ?? 'Job completed but no MusicXML was produced (check transcription/notation).',
            )
          }
        }
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Failed to poll job status.'
        setUploadState({ phase: 'error', message })
        clearPollTimer()
      }
    },
    [clearPollTimer, loadScore],
  )

  const startPolling = useCallback(
    (jobId: string) => {
      clearPollTimer()
      void pollJobStatus(jobId)
      pollTimerRef.current = window.setInterval(() => {
        void pollJobStatus(jobId)
      }, POLL_INTERVAL_MS)
    },
    [clearPollTimer, pollJobStatus],
  )

  const uploadFile = useCallback(
    async (file: File) => {
      const validationError = validateClientWavFile(file)
      if (validationError) {
        setUploadState({ phase: 'error', message: validationError })
        return
      }

      setJobStatus(null)
      setMusicXml(null)
      setScoreError(null)
      setUploadState({
        phase: 'uploading',
        fileName: file.name,
        progress: { loaded: 0, total: file.size, percent: 0 },
      })

      try {
        const response = await uploadWavFile(file, (progress) => {
          setUploadState({
            phase: 'uploading',
            fileName: file.name,
            progress,
          })
        })

        setUploadState({
          phase: 'success',
          jobId: response.job_id,
          message: response.message,
        })
        startPolling(response.job_id)
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Upload failed.'
        setUploadState({ phase: 'error', message })
      }
    },
    [startPolling],
  )

  const reset = useCallback(() => {
    clearPollTimer()
    setUploadState({ phase: 'idle' })
    setJobStatus(null)
    setMusicXml(null)
    setScoreError(null)
    setIsFetchingScore(false)
  }, [clearPollTimer])

  useEffect(() => clearPollTimer, [clearPollTimer])

  const isProcessing = jobStatus ? PROCESSING_STATUSES.has(jobStatus.status) : false

  return {
    uploadState,
    jobStatus,
    musicXml,
    scoreError,
    isFetchingScore,
    isProcessing,
    uploadFile,
    reset,
  }
}
