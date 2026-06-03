// AI-assisted: ScoreFlow app shell — warm sandy neumorphic DAW layout.

import { useState } from 'react'

import type Embed from 'flat-embed'

import { DawTrackStack } from './components/DawTrackStack'
import { PipelineStatus } from './components/PipelineStatus'
import { ScoreWorkspace } from './components/ScoreWorkspace'
import { TransportBar } from './components/TransportBar'
import { UploadZone } from './components/UploadZone'
import { usePipeline } from './hooks/usePipeline'
import type { StemTrackId } from './theme/stems'

function App() {
  const {
    uploadState,
    jobStatus,
    musicXml,
    scoreError,
    isFetchingScore,
    isProcessing,
    uploadFile,
    reset,
  } = usePipeline()
  const [playingStem, setPlayingStem] = useState<StemTrackId | null>(null)
  const [flatEmbed, setFlatEmbed] = useState<Embed | null>(null)

  return (
    <main className="sf-app-shell min-h-screen px-4 pb-32 pt-10">
      <div className="mx-auto flex max-w-4xl flex-col items-center text-center">
        <p className="sf-label">ScoreFlow</p>
        <h1 className="sf-heading mt-2 text-4xl">Upload your recording</h1>
        <p className="sf-text-muted mt-3 max-w-xl">
          Upload a WAV to separate stems, transcribe each part, edit the SATB score, and prepare it
          for export.
        </p>

        <div className="mt-10 flex w-full justify-center">
          <UploadZone uploadState={uploadState} onFileSelected={uploadFile} onReset={reset} />
        </div>

        {(uploadState.phase === 'success' || jobStatus) && (
          <>
            <PipelineStatus jobStatus={jobStatus} />

            <ScoreWorkspace
              pipelineMusicXml={musicXml}
              scoreError={scoreError}
              isPipelineComplete={jobStatus?.status === 'completed'}
              isProcessing={isProcessing}
              isFetchingScore={isFetchingScore}
              pipelineStatus={jobStatus?.status ?? null}
              jobFilename={jobStatus?.original_filename ?? null}
              onEmbedReady={setFlatEmbed}
            />

            {jobStatus?.demucs_stems &&
              (jobStatus.status === 'completed' ||
                jobStatus.status === 'transcribing' ||
                jobStatus.status === 'notating') && (
              <DawTrackStack
                jobStatus={jobStatus}
                playingStem={playingStem}
                onPlayStem={setPlayingStem}
              />
            )}
          </>
        )}
      </div>

      <TransportBar
        flatEmbed={flatEmbed}
        selectedStem={playingStem}
        jobId={jobStatus?.job_id ?? null}
      />
    </main>
  )
}

export default App
