# AI-assisted: Milestone 3 orchestrator — separation → transcription → notation pipeline.

import logging
from pathlib import Path

from app.models.job import JobStatus
from app.config import get_settings
from app.pipeline.notation import build_satb_score
from app.pipeline.separation import separate_audio
from app.pipeline.transcription import transcribe_stems
from app.utils.audio_trim import trim_wav_to_max_seconds
from app.utils.job_store import job_store

logger = logging.getLogger(__name__)


def _merge_warnings(existing: list[str], new: list[str]) -> list[str]:
    """Combine warning lists without duplicates."""
    combined = list(existing)
    for warning in new:
        if warning not in combined:
            combined.append(warning)
    return combined


def process_upload_job(job_id: str) -> None:
    """
    Background task invoked after upload completes.

    Runs separation, transcription, and notation without blocking HTTP.
    """
    try:
        _run_upload_pipeline(job_id)
    except Exception as exc:
        logger.exception("Pipeline crashed for job_id=%s", job_id)
        job = job_store.get(job_id)
        if job is not None and job.status not in (JobStatus.FAILED, JobStatus.COMPLETED):
            job_store.update_job(
                job_id,
                status=JobStatus.FAILED,
                error=f"Pipeline error: {exc}",
            )


def _run_upload_pipeline(job_id: str) -> None:
    job = job_store.get(job_id)
    if job is None:
        logger.error("Background task could not find job_id=%s", job_id)
        return

    stored_path = Path(job.stored_path)
    if not stored_path.is_file():
        job_store.update_status(job_id, JobStatus.FAILED, error="Uploaded file missing on disk.")
        return

    settings = get_settings()
    pipeline_input, trim_warning = trim_wav_to_max_seconds(
        stored_path,
        settings.pipeline_max_audio_seconds,
    )
    job_warnings = list(job.warnings)
    if trim_warning:
        job_warnings = _merge_warnings(job_warnings, [trim_warning])

    job_store.update_job(job_id, status=JobStatus.SEPARATING, warnings=job_warnings)
    logger.info("Starting separation for job_id=%s at %s", job_id, pipeline_input)

    separation_result = separate_audio(job_id=job_id, input_path=pipeline_input)
    if not separation_result.success:
        job_store.update_job(
            job_id,
            status=JobStatus.FAILED,
            error=separation_result.error or "Source separation failed.",
            warnings=_merge_warnings(job_warnings, separation_result.warnings),
        )
        return

    job_store.update_job(
        job_id,
        status=JobStatus.TRANSCRIBING,
        stems_dir=separation_result.output_dir,
        demucs_stems=separation_result.demucs_stems,
        satb_stems=separation_result.satb_stems,
        warnings=_merge_warnings(job_warnings, separation_result.warnings),
    )

    transcription_result = transcribe_stems(job_id=job_id, stem_paths=separation_result.demucs_stems)
    if not transcription_result.success:
        current = job_store.get(job_id)
        job_store.update_job(
            job_id,
            status=JobStatus.FAILED,
            error=transcription_result.error or "Transcription failed.",
            warnings=_merge_warnings(current.warnings if current else [], transcription_result.warnings),
        )
        return

    current = job_store.get(job_id)
    job_store.update_job(
        job_id,
        status=JobStatus.NOTATING,
        midi_paths=transcription_result.midi_paths,
        warnings=_merge_warnings(current.warnings if current else [], transcription_result.warnings),
    )

    notation_result = build_satb_score(job_id=job_id, midi_paths=transcription_result.midi_paths)
    if not notation_result.success:
        current = job_store.get(job_id)
        job_store.update_job(
            job_id,
            status=JobStatus.FAILED,
            error=notation_result.error or "Notation failed.",
            warnings=_merge_warnings(current.warnings if current else [], notation_result.warnings),
        )
        return

    current = job_store.get(job_id)
    job_store.update_job(
        job_id,
        status=JobStatus.COMPLETED,
        music_xml=notation_result.music_xml,
        warnings=_merge_warnings(current.warnings if current else [], notation_result.warnings),
        error=None,
    )
    logger.info("Pipeline complete for job_id=%s", job_id)
