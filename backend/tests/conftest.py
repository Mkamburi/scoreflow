"""Shared helpers for backend tests."""

import io
import struct
import wave


def make_test_wav(
    *,
    duration_sec: float = 1.0,
    sample_rate: int = 44100,
    channels: int = 1,
    frequency_hz: int = 440,
) -> bytes:
    """Build a small mono/stereo sine-wave WAV for integration tests."""
    frame_count = int(duration_sec * sample_rate)
    buffer = io.BytesIO()

    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)

        frames = bytearray()
        for index in range(frame_count):
            sample = int(32767 * 0.2 * __import__("math").sin(2 * __import__("math").pi * frequency_hz * index / sample_rate))
            frame = struct.pack("<h", sample)
            frames.extend(frame * channels)

        wav_file.writeframes(bytes(frames))

    return buffer.getvalue()
