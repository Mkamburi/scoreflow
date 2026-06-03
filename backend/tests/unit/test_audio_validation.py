# backend/tests/unit/test_audio_validation.py

import struct

import pytest

from app.utils.audio_validation import validate_wav_upload


def _wav_header(*, channels: int = 1, sample_rate: int = 44100) -> bytes:
    header = bytearray(b"RIFF" + b"\x00" * 4 + b"WAVEfmt " + b"\x00" * 12)
    header.extend(b"\x00" * 16)
    header[22:24] = struct.pack("<H", channels)
    header[24:28] = struct.pack("<I", sample_rate)
    return bytes(header[:44])


def test_validate_wav_upload_accepts_valid_mono_wav() -> None:
    result = validate_wav_upload(
        filename="recording.wav",
        content_type="audio/wav",
        size_bytes=1024,
        max_size_bytes=50 * 1024 * 1024,
        header_bytes=_wav_header(),
    )

    assert result.is_valid is True
    assert result.channels == 1
    assert result.sample_rate == 44100


def test_validate_wav_upload_rejects_non_wav_extension() -> None:
    result = validate_wav_upload(
        filename="recording.mp3",
        content_type="audio/mpeg",
        size_bytes=1024,
        max_size_bytes=50 * 1024 * 1024,
        header_bytes=_wav_header(),
    )

    assert result.is_valid is False
    assert result.error is not None
    assert ".wav" in result.error


def test_validate_wav_upload_rejects_oversized_file() -> None:
    result = validate_wav_upload(
        filename="recording.wav",
        content_type="audio/wav",
        size_bytes=60 * 1024 * 1024,
        max_size_bytes=50 * 1024 * 1024,
        header_bytes=_wav_header(),
    )

    assert result.is_valid is False
    assert "50 MB" in (result.error or "")


def test_validate_wav_upload_rejects_invalid_header() -> None:
    result = validate_wav_upload(
        filename="recording.wav",
        content_type="audio/wav",
        size_bytes=1024,
        max_size_bytes=50 * 1024 * 1024,
        header_bytes=b"NOT-A-WAV-FILE" + b"\x00" * 30,
    )

    assert result.is_valid is False
    assert result.error is not None
