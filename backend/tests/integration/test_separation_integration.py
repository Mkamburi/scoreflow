# backend/tests/integration/test_separation.py

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.pipeline.separation import separate_audio
from tests.conftest import make_test_wav


@patch("app.pipeline.separation._run_demucs_subprocess")
def test_separate_audio_with_real_wav_fixture(
    mock_run_demucs: MagicMock,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Integration-style test using a real short WAV and mocked Demucs CLI output."""
    stems_dir = tmp_path / "stems"
    monkeypatch.setenv("STEMS_DIR", str(stems_dir))
    from app.config import get_settings

    get_settings.cache_clear()

    wav_path = tmp_path / "test_mono_5s.wav"
    wav_path.write_bytes(make_test_wav(duration_sec=0.5))

    mock_run_demucs.return_value = MagicMock(returncode=0, stderr="", stdout="ok")

    track_dir = stems_dir / "integration-job" / "htdemucs" / "test_mono_5s"
    track_dir.mkdir(parents=True)
    for stem_name in ("vocals", "drums", "bass", "other"):
        (track_dir / f"{stem_name}.wav").write_bytes(wav_path.read_bytes())

    result = separate_audio("integration-job", wav_path)

    assert result.success is True
    assert len(result.demucs_stems) == 4
    assert result.satb_stems["bass"] == result.demucs_stems["bass"]
    assert result.warnings
