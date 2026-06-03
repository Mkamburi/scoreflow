# backend/tests/unit/test_separation.py

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.pipeline.separation import (
    DEMUCS_STEM_NAMES,
    STEM_BLEED_WARNING,
    _collect_demucs_stems,
    map_stems_to_satb,
    separate_audio,
)


def test_map_stems_to_satb_assigns_provisional_roles() -> None:
    demucs_stems = {
        "vocals": "/tmp/vocals.wav",
        "drums": "/tmp/drums.wav",
        "bass": "/tmp/bass.wav",
        "other": "/tmp/other.wav",
    }

    satb = map_stems_to_satb(demucs_stems)

    assert satb["soprano"] == "/tmp/vocals.wav"
    assert satb["alto"] == "/tmp/vocals.wav"
    assert satb["tenor"] == "/tmp/other.wav"
    assert satb["bass"] == "/tmp/bass.wav"
    assert satb["percussion"] == "/tmp/drums.wav"


def test_collect_demucs_stems_requires_all_stems(tmp_path: Path) -> None:
    track_dir = tmp_path / "htdemucs" / "demo"
    track_dir.mkdir(parents=True)
    for stem_name in DEMUCS_STEM_NAMES:
        (track_dir / f"{stem_name}.wav").write_bytes(b"RIFF")

    stems = _collect_demucs_stems(track_dir)

    assert set(stems.keys()) == set(DEMUCS_STEM_NAMES)


def test_collect_demucs_stems_raises_when_stem_missing(tmp_path: Path) -> None:
    track_dir = tmp_path / "htdemucs" / "demo"
    track_dir.mkdir(parents=True)
    (track_dir / "vocals.wav").write_bytes(b"RIFF")

    with pytest.raises(FileNotFoundError):
        _collect_demucs_stems(track_dir)


@patch("app.pipeline.separation._run_demucs_subprocess")
def test_separate_audio_success(
    mock_run_demucs: MagicMock,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("STEMS_DIR", str(tmp_path / "stems"))
    from app.config import get_settings

    get_settings.cache_clear()

    input_path = tmp_path / "job-123.wav"
    input_path.write_bytes(b"RIFF" + b"\x00" * 128)

    mock_run_demucs.return_value = MagicMock(returncode=0, stderr="", stdout="done")

    track_dir = tmp_path / "stems" / "job-123" / "htdemucs" / "job-123"
    track_dir.mkdir(parents=True)
    for stem_name in DEMUCS_STEM_NAMES:
        (track_dir / f"{stem_name}.wav").write_bytes(b"RIFF")

    result = separate_audio("job-123", input_path)

    assert result.success is True
    assert result.demucs_stems["vocals"] == str(track_dir / "vocals.wav")
    assert result.satb_stems["tenor"] == str(track_dir / "other.wav")
    assert STEM_BLEED_WARNING in result.warnings
    mock_run_demucs.assert_called_once()


@patch("app.pipeline.separation._run_demucs_subprocess")
def test_separate_audio_returns_structured_error_when_demucs_fails(
    mock_run_demucs: MagicMock,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("STEMS_DIR", str(tmp_path / "stems"))
    from app.config import get_settings

    get_settings.cache_clear()

    input_path = tmp_path / "job-456.wav"
    input_path.write_bytes(b"RIFF" + b"\x00" * 128)
    mock_run_demucs.return_value = MagicMock(returncode=1, stderr="boom", stdout="")

    result = separate_audio("job-456", input_path)

    assert result.success is False
    assert result.error == "Demucs source separation failed: boom"
    assert result.stderr == "boom"


def test_separate_audio_returns_error_for_missing_input(tmp_path: Path) -> None:
    result = separate_audio("job-789", tmp_path / "missing.wav")

    assert result.success is False
    assert "not found" in (result.error or "").lower()
