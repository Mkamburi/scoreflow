import wave
from pathlib import Path

import numpy as np
import pytest

from app.utils.audio_trim import trim_wav_to_max_seconds


def _write_wav(path: Path, *, duration_sec: float, sample_rate: int = 22050) -> None:
    frames = int(duration_sec * sample_rate)
    samples = (np.sin(np.linspace(0, 8 * np.pi, frames)) * 16000).astype(np.int16)
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(samples.tobytes())


def test_trim_wav_leaves_short_files_untouched(tmp_path: Path) -> None:
    wav_path = tmp_path / "short.wav"
    _write_wav(wav_path, duration_sec=1.0)

    result_path, warning = trim_wav_to_max_seconds(wav_path, max_seconds=120)

    assert result_path == wav_path
    assert warning is None


def test_trim_wav_caps_long_files(tmp_path: Path) -> None:
    wav_path = tmp_path / "long.wav"
    _write_wav(wav_path, duration_sec=5.0)

    result_path, warning = trim_wav_to_max_seconds(wav_path, max_seconds=2.0)

    assert result_path != wav_path
    assert result_path.is_file()
    assert warning is not None
    assert "2" in warning

    import soundfile as sf

    data, sample_rate = sf.read(str(result_path))
    assert data.shape[0] <= int(2.0 * sample_rate) + 1
