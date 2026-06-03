# backend/tests/integration/test_orchestrator.py

from pathlib import Path
from unittest.mock import patch

import pytest

from app.models.job import JobRecord, JobStatus
from app.models.notation import NotationResult
from app.models.separation import SeparationResult
from app.models.transcription import TranscriptionResult
from app.pipeline.orchestrator import process_upload_job
from app.utils.job_store import job_store


@patch("app.pipeline.orchestrator.build_satb_score")
@patch("app.pipeline.orchestrator.transcribe_stems")
@patch("app.pipeline.orchestrator.separate_audio")
def test_process_upload_job_runs_full_pipeline(
    mock_separate_audio,
    mock_transcribe_stems,
    mock_build_satb_score,
    tmp_path: Path,
) -> None:
    wav_path = tmp_path / "job.wav"
    wav_path.write_bytes(b"RIFF" + b"\x00" * 128)

    job_id = "orch-test-job"
    job_store.create(
        JobRecord(
            job_id=job_id,
            status=JobStatus.QUEUED,
            original_filename="job.wav",
            stored_path=str(wav_path),
            size_bytes=wav_path.stat().st_size,
        )
    )

    mock_separate_audio.return_value = SeparationResult(
        success=True,
        job_id=job_id,
        input_path=str(wav_path),
        output_dir=str(tmp_path / "stems" / job_id),
        demucs_stems={
            "vocals": str(tmp_path / "vocals.wav"),
            "drums": str(tmp_path / "drums.wav"),
            "bass": str(tmp_path / "bass.wav"),
            "other": str(tmp_path / "other.wav"),
        },
        satb_stems={
            "soprano": str(tmp_path / "vocals.wav"),
            "alto": str(tmp_path / "vocals.wav"),
            "tenor": str(tmp_path / "other.wav"),
            "bass": str(tmp_path / "bass.wav"),
            "percussion": str(tmp_path / "drums.wav"),
        },
        warnings=["stem bleed warning"],
    )
    mock_transcribe_stems.return_value = TranscriptionResult(
        success=True,
        job_id=job_id,
        output_dir=str(tmp_path / "midi" / job_id),
        midi_paths={
            "vocals": str(tmp_path / "vocals.mid"),
            "other": str(tmp_path / "other.mid"),
            "bass": str(tmp_path / "bass.mid"),
        },
        warnings=["drums skipped"],
    )
    mock_build_satb_score.return_value = NotationResult(
        success=True,
        job_id=job_id,
        music_xml='<?xml version="1.0"?><score-partwise version="3.1"><part-list/></score-partwise>',
        warnings=["vocal split"],
    )

    process_upload_job(job_id)

    updated = job_store.get(job_id)
    assert updated is not None
    assert updated.status == JobStatus.COMPLETED
    assert updated.music_xml is not None
    assert updated.midi_paths is not None
    mock_separate_audio.assert_called_once()
    mock_transcribe_stems.assert_called_once()
    mock_build_satb_score.assert_called_once()
