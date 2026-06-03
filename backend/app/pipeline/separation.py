# AI-assisted: Milestone 2 Demucs separation — subprocess htdemucs with SATB stem mapping.
# Uses subprocess so the HTTP thread is never blocked; orchestrator calls this from a background task.

import logging
import subprocess
from pathlib import Path

from app.config import get_settings
from app.models.separation import SeparationResult

logger = logging.getLogger(__name__)

DEMUCS_MODEL = "htdemucs"
DEMUCS_STEM_NAMES = ("vocals", "drums", "bass", "other")

# MUSICAL NOTE: Demucs stem bleed is common — bass energy often leaks into "other"
# (and vice versa). Downstream Basic Pitch transcription may sound muddy or assign
# notes to the wrong SATB part; manual score editing (Milestone 3.5) compensates.
STEM_BLEED_WARNING = (
    "Demucs may bleed bass frequencies into the 'other' stem and vice versa. "
    "If transcription sounds off, stem bleed is the usual cause."
)

# Provisional SATB mapping at separation time. Soprano/alto share the vocals stem
# until pitch-range splitting during transcription (Milestone 3).
SATB_ROLE_TO_DEMUCS_STEM: dict[str, str | None] = {
    "soprano": "vocals",
    "alto": "vocals",
    "tenor": "other",
    "bass": "bass",
    "percussion": "drums",
}


def _resolve_stems_output_dir(job_id: str, output_dir: Path | None = None) -> Path:
    """Return the directory where Demucs stems for this job should be written."""
    settings = get_settings()
    base_dir = output_dir or Path(settings.stems_dir)
    return base_dir / job_id


def _resolve_demucs_track_dir(output_dir: Path, input_path: Path) -> Path:
    """Return the directory Demucs creates for a given input track."""
    track_name = input_path.stem
    return output_dir / DEMUCS_MODEL / track_name


def _collect_demucs_stems(track_dir: Path) -> dict[str, str]:
    """
    Collect absolute paths to Demucs stem WAV files.

    Raises FileNotFoundError if any expected stem is missing.
    """
    stems: dict[str, str] = {}
    for stem_name in DEMUCS_STEM_NAMES:
        stem_path = track_dir / f"{stem_name}.wav"
        if not stem_path.is_file():
            raise FileNotFoundError(f"Missing expected Demucs stem: {stem_path}")
        stems[stem_name] = str(stem_path)
    return stems


def map_stems_to_satb(demucs_stems: dict[str, str]) -> dict[str, str | None]:
    """
    Map Demucs 4-stem output to provisional SATB (+ percussion) roles.

    Soprano and alto both reference the vocals stem until Milestone 3 splits by pitch.
    """
    satb_stems: dict[str, str | None] = {}
    for role, demucs_name in SATB_ROLE_TO_DEMUCS_STEM.items():
        if demucs_name is None:
            satb_stems[role] = None
            continue
        satb_stems[role] = demucs_stems.get(demucs_name)
    return satb_stems


def _format_demucs_error(stderr: str) -> str:
    """Turn Demucs stderr into a user-actionable error message."""
    lowered = stderr.lower()
    if "no module named 'torchcodec'" in lowered or "torchcodec is required" in lowered:
        return (
            "Demucs failed: missing torchcodec. "
            "Run: pip install torchcodec soundfile"
        )
    if "libavutil" in lowered or "libtorchcodec" in lowered or "ffmpeg" in lowered:
        return (
            "Demucs failed: ffmpeg libraries are required. "
            "On macOS run: brew install ffmpeg"
        )
    if "demucs cli not found" in lowered:
        return "Demucs CLI not found. Install with: pip install demucs"
    first_line = next((line.strip() for line in stderr.splitlines() if line.strip()), "")
    if first_line:
        return f"Demucs source separation failed: {first_line}"
    return "Demucs source separation failed."


def _run_demucs_subprocess(input_path: Path, output_dir: Path) -> subprocess.CompletedProcess[str]:
    """Invoke the Demucs CLI in a subprocess."""
    output_dir.mkdir(parents=True, exist_ok=True)
    command = [
        "demucs",
        "-n",
        DEMUCS_MODEL,
        "--out",
        str(output_dir),
        str(input_path),
    ]
    logger.info("Running Demucs command: %s", " ".join(command))
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
        timeout=get_settings().separation_timeout_sec,
    )


def separate_audio(
    job_id: str,
    input_path: str | Path,
    output_dir: str | Path | None = None,
) -> SeparationResult:
    """
    Run htdemucs on an uploaded WAV and return structured stem paths.

    Args:
        job_id: Upload job identifier used for output directory naming.
        input_path: Absolute path to the uploaded WAV file.
        output_dir: Optional override for the parent stems directory.

    Returns:
        SeparationResult with Demucs stem paths and provisional SATB mapping.
    """
    input_file = Path(input_path)
    stems_output_dir = _resolve_stems_output_dir(job_id, Path(output_dir) if output_dir else None)
    warnings = [STEM_BLEED_WARNING]

    if not input_file.is_file():
        return SeparationResult(
            success=False,
            job_id=job_id,
            input_path=str(input_file),
            warnings=warnings,
            error=f"Input audio file not found: {input_file}",
        )

    try:
        completed = _run_demucs_subprocess(input_file, stems_output_dir)
    except FileNotFoundError:
        return SeparationResult(
            success=False,
            job_id=job_id,
            input_path=str(input_file),
            warnings=warnings,
            error="Demucs CLI not found. Install with: pip install demucs",
        )
    except subprocess.TimeoutExpired:
        return SeparationResult(
            success=False,
            job_id=job_id,
            input_path=str(input_file),
            output_dir=str(stems_output_dir),
            warnings=warnings,
            error=f"Demucs timed out after {get_settings().separation_timeout_sec} seconds.",
        )
    except OSError as exc:
        logger.exception("Demucs subprocess failed for job_id=%s", job_id)
        return SeparationResult(
            success=False,
            job_id=job_id,
            input_path=str(input_file),
            output_dir=str(stems_output_dir),
            warnings=warnings,
            error=f"Failed to run Demucs subprocess: {exc}",
        )

    if completed.returncode != 0:
        stderr = (completed.stderr or "").strip()
        logger.error("Demucs failed for job_id=%s: %s", job_id, stderr)
        return SeparationResult(
            success=False,
            job_id=job_id,
            input_path=str(input_file),
            output_dir=str(stems_output_dir),
            warnings=warnings,
            error=_format_demucs_error(stderr),
            stderr=stderr or None,
        )

    try:
        track_dir = _resolve_demucs_track_dir(stems_output_dir, input_file)
        demucs_stems = _collect_demucs_stems(track_dir)
        satb_stems = map_stems_to_satb(demucs_stems)
    except FileNotFoundError as exc:
        logger.exception("Demucs output incomplete for job_id=%s", job_id)
        return SeparationResult(
            success=False,
            job_id=job_id,
            input_path=str(input_file),
            output_dir=str(stems_output_dir),
            warnings=warnings,
            error=str(exc),
            stderr=(completed.stderr or "").strip() or None,
        )

    logger.info("Separation complete for job_id=%s in %s", job_id, stems_output_dir)
    return SeparationResult(
        success=True,
        job_id=job_id,
        input_path=str(input_file),
        output_dir=str(stems_output_dir),
        model_name=DEMUCS_MODEL,
        demucs_stems=demucs_stems,
        satb_stems=satb_stems,
        warnings=warnings,
        stderr=(completed.stderr or "").strip() or None,
    )


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        raise SystemExit("Usage: python -m app.pipeline.separation <job_id> <path/to/input.wav>")

    smoke_job_id, smoke_input = sys.argv[1], sys.argv[2]
    result = separate_audio(smoke_job_id, smoke_input)
    print(result.model_dump_json(indent=2))
    if not result.success:
        raise SystemExit(1)
