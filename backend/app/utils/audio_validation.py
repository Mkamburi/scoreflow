# AI-assisted: Milestone 1 WAV validation — MIME, extension, size, and RIFF header checks.

import struct
from dataclasses import dataclass

ALLOWED_EXTENSIONS = {".wav"}
ALLOWED_CONTENT_TYPES = {
    "audio/wav",
    "audio/x-wav",
    "audio/wave",
    "audio/vnd.wave",
}


@dataclass(frozen=True)
class AudioValidationResult:
    """Outcome of validating an uploaded audio file."""

    is_valid: bool
    error: str | None = None
    sample_rate: int | None = None
    channels: int | None = None


def _extension(filename: str) -> str:
    """Return lowercase file extension including the dot."""
    dot_index = filename.rfind(".")
    if dot_index == -1:
        return ""
    return filename[dot_index:].lower()


def validate_wav_upload(
    *,
    filename: str,
    content_type: str | None,
    size_bytes: int,
    max_size_bytes: int,
    header_bytes: bytes,
) -> AudioValidationResult:
    """
    Validate an uploaded WAV file before persisting it.

    Checks extension, MIME type, size limit, and basic RIFF/WAVE structure.
    """
    extension = _extension(filename)
    if extension not in ALLOWED_EXTENSIONS:
        return AudioValidationResult(
            is_valid=False,
            error="Only .wav files are supported.",
        )

    normalized_content_type = (content_type or "").split(";")[0].strip().lower()
    if normalized_content_type and normalized_content_type not in ALLOWED_CONTENT_TYPES:
        return AudioValidationResult(
            is_valid=False,
            error=f"Unsupported content type: {normalized_content_type}.",
        )

    if size_bytes <= 0:
        return AudioValidationResult(is_valid=False, error="Uploaded file is empty.")

    if size_bytes > max_size_bytes:
        max_mb = max_size_bytes // (1024 * 1024)
        return AudioValidationResult(
            is_valid=False,
            error=f"File exceeds the {max_mb} MB upload limit.",
        )

    if len(header_bytes) < 44:
        return AudioValidationResult(
            is_valid=False,
            error="File is too small to be a valid WAV.",
        )

    if header_bytes[0:4] != b"RIFF" or header_bytes[8:12] != b"WAVE":
        return AudioValidationResult(
            is_valid=False,
            error="File does not appear to be a valid WAV (missing RIFF/WAVE header).",
        )

    try:
        channels = struct.unpack("<H", header_bytes[22:24])[0]
        sample_rate = struct.unpack("<I", header_bytes[24:28])[0]
    except struct.error:
        return AudioValidationResult(
            is_valid=False,
            error="Could not parse WAV header.",
        )

    if channels not in (1, 2):
        return AudioValidationResult(
            is_valid=False,
            error=f"Unsupported channel count: {channels}. Expected mono or stereo.",
        )

    if sample_rate <= 0:
        return AudioValidationResult(
            is_valid=False,
            error="Invalid sample rate in WAV header.",
        )

    return AudioValidationResult(
        is_valid=True,
        sample_rate=sample_rate,
        channels=channels,
    )


if __name__ == "__main__":
    header = b"RIFF" + b"\x00" * 4 + b"WAVE" + b"\x00" * 16
    header = header[:22] + struct.pack("<H", 1) + struct.pack("<I", 44100)
    result = validate_wav_upload(
        filename="test.wav",
        content_type="audio/wav",
        size_bytes=1024,
        max_size_bytes=50 * 1024 * 1024,
        header_bytes=header + b"\x00" * 12,
    )
    assert result.is_valid, result.error
    print("audio_validation smoke test passed")
