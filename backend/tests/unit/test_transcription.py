# backend/tests/unit/test_transcription.py

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.pipeline.transcription import (
    DRUMS_SKIPPED_WARNING,
    TRANSCRIPTION_STEMS,
    _find_midi_file,
    transcribe_stems,
)


def test_find_midi_file_prefers_basic_pitch_naming(tmp_path: Path) -> None:
    stem_dir = tmp_path / "vocals"
    stem_dir.mkdir()
    midi_path = stem_dir / "vocals_basic_pitch.mid"
    midi_path.write_bytes(b"MThd")

    assert _find_midi_file(stem_dir, "vocals") == midi_path


@patch("app.pipeline.transcription._run_basic_pitch")
def test_transcribe_stems_success(
    mock_run_basic_pitch: MagicMock,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MIDI_DIR", str(tmp_path / "midi"))
    from app.config import get_settings

    get_settings.cache_clear()

    stem_paths = {}
    for stem_name in TRANSCRIPTION_STEMS:
        wav_path = tmp_path / f"{stem_name}.wav"
        wav_path.write_bytes(b"RIFF" + b"\x00" * 44)
        stem_paths[stem_name] = str(wav_path)

    def _write_midi(wav_path: Path, output_dir: Path) -> None:
        stem_name = wav_path.stem
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / f"{stem_name}_basic_pitch.mid").write_bytes(b"MThd")

    mock_run_basic_pitch.side_effect = _write_midi

    result = transcribe_stems("job-transcribe-1", stem_paths)

    assert result.success is True
    assert set(result.midi_paths.keys()) == set(TRANSCRIPTION_STEMS)
    assert DRUMS_SKIPPED_WARNING in result.warnings
    assert mock_run_basic_pitch.call_count == 3


def test_transcribe_stems_returns_error_when_required_stem_missing(tmp_path: Path) -> None:
    result = transcribe_stems(
        "job-transcribe-2",
        {"vocals": str(tmp_path / "vocals.wav")},
    )

    assert result.success is False
    assert "Missing required stems" in (result.error or "")


@patch("app.pipeline.transcription._run_basic_pitch")
def test_transcribe_stems_returns_error_when_midi_output_missing(
    mock_run_basic_pitch: MagicMock,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MIDI_DIR", str(tmp_path / "midi"))
    from app.config import get_settings

    get_settings.cache_clear()

    stem_paths = {}
    for stem_name in TRANSCRIPTION_STEMS:
        wav_path = tmp_path / f"{stem_name}.wav"
        wav_path.write_bytes(b"RIFF" + b"\x00" * 44)
        stem_paths[stem_name] = str(wav_path)

    mock_run_basic_pitch.return_value = None

    result = transcribe_stems("job-transcribe-4", stem_paths)

    assert result.success is False
    assert "no MIDI was found" in (result.error or "")


@patch("app.pipeline.transcription._run_basic_pitch")
def test_transcribe_stems_returns_structured_error_when_basic_pitch_fails(
    mock_run_basic_pitch: MagicMock,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MIDI_DIR", str(tmp_path / "midi"))
    from app.config import get_settings

    get_settings.cache_clear()

    stem_paths = {}
    for stem_name in TRANSCRIPTION_STEMS:
        wav_path = tmp_path / f"{stem_name}.wav"
        wav_path.write_bytes(b"RIFF" + b"\x00" * 44)
        stem_paths[stem_name] = str(wav_path)

    mock_run_basic_pitch.side_effect = RuntimeError("model failed")

    result = transcribe_stems("job-transcribe-3", stem_paths)

    assert result.success is False
    assert "model failed" in (result.error or "")
