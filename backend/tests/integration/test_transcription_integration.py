# backend/tests/integration/test_transcription_integration.py

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.pipeline.transcription import transcribe_stems
from tests.conftest import make_test_wav


@patch("app.pipeline.transcription._run_basic_pitch_subprocess")
def test_transcribe_stems_with_real_wav_fixture(
    mock_run_basic_pitch: MagicMock,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Integration-style test using a real short WAV on disk.

    Basic Pitch is mocked to keep CI fast, but the WAV fixture is a genuine file
    read from disk as in production.
    """
    monkeypatch.setenv("MIDI_DIR", str(tmp_path / "midi"))
    from app.config import get_settings

    get_settings.cache_clear()

    wav_bytes = make_test_wav(duration_sec=0.5, frequency_hz=440)
    stem_paths: dict[str, str] = {}
    for stem_name in ("vocals", "other", "bass"):
        wav_path = tmp_path / f"{stem_name}.wav"
        wav_path.write_bytes(wav_bytes)
        stem_paths[stem_name] = str(wav_path)

    def _write_midi(wav_path: Path, output_dir: Path) -> MagicMock:
        stem_name = wav_path.stem
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / f"{stem_name}_basic_pitch.mid").write_bytes(b"MThd" + b"\x00" * 12)
        return MagicMock(returncode=0, stderr="", stdout="ok")

    mock_run_basic_pitch.side_effect = _write_midi

    result = transcribe_stems("integration-transcription-job", stem_paths)

    assert result.success is True
    assert len(result.midi_paths) == 3
    for stem_name, midi_path in result.midi_paths.items():
        assert Path(midi_path).is_file()
        assert stem_name in Path(midi_path).name
