# AI-assisted: Trim long uploads before Demucs/Basic Pitch to keep pipeline times reasonable.

import logging
from pathlib import Path

import soundfile as sf

logger = logging.getLogger(__name__)

TRIM_WARNING_TEMPLATE = (
    "Audio trimmed to the first {seconds:g} seconds for faster processing "
    "(upload was longer)."
)


def trim_wav_to_max_seconds(
    input_path: Path,
    max_seconds: float,
) -> tuple[Path, str | None]:
    """
    Return a path to audio capped at max_seconds.

    If the file is already shorter, returns the original path and no warning.
    """
    if max_seconds <= 0:
        return input_path, None

    data, sample_rate = sf.read(str(input_path), always_2d=True)
    max_frames = int(max_seconds * sample_rate)
    if data.shape[0] <= max_frames:
        return input_path, None

    trimmed_path = input_path.with_name(f"{input_path.stem}_trimmed{input_path.suffix}")
    sf.write(str(trimmed_path), data[:max_frames], sample_rate, subtype="PCM_16")
    warning = TRIM_WARNING_TEMPLATE.format(seconds=max_seconds)
    logger.info(
        "Trimmed %s from %.1fs to %.1fs -> %s",
        input_path,
        data.shape[0] / sample_rate,
        max_seconds,
        trimmed_path,
    )
    return trimmed_path, warning
