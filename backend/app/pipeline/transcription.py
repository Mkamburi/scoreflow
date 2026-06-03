# AI-assisted: Milestone 3 Basic Pitch transcription — stem WAVs to MIDI via subprocess.
# Invoked from the orchestrator background task; never blocks the HTTP thread.

import logging
import sys
from pathlib import Path

from app.config import get_settings
from app.models.transcription import TranscriptionResult

try:
    from basic_pitch import ICASSP_2022_MODEL_PATH
    from basic_pitch.inference import predict_and_save as basic_pitch_predict_and_save
except ImportError:  # pragma: no cover - optional until install_basic_pitch.sh runs
    ICASSP_2022_MODEL_PATH = None
    basic_pitch_predict_and_save = None

logger = logging.getLogger(__name__)

# MUSICAL NOTE: We transcribe vocals, other (tenor proxy), and bass only.
# Drums are omitted from notation — unpitched percussion does not map cleanly to SATB.
TRANSCRIPTION_STEMS = ("vocals", "other", "bass")

DRUMS_SKIPPED_WARNING = (
    "Drums stem was intentionally skipped. Unpitched percussion is omitted from SATB notation."
)


def _resolve_midi_output_dir(job_id: str, output_dir: Path | None = None) -> Path:
    """Return the parent directory for all MIDI files belonging to a job."""
    settings = get_settings()
    base_dir = output_dir or Path(settings.midi_dir)
    return base_dir / job_id


def _resolve_stem_midi_dir(job_output_dir: Path, stem_name: str) -> Path:
    """Return the output directory for a single stem's Basic Pitch run."""
    return job_output_dir / stem_name


def _find_midi_file(stem_output_dir: Path, stem_name: str) -> Path:
    """
    Locate the MIDI file Basic Pitch wrote for a stem.

    Basic Pitch naming varies by version; check common patterns then glob.
    """
    candidates = [
        stem_output_dir / f"{stem_name}_basic_pitch.mid",
        stem_output_dir / stem_name / f"{stem_name}_basic_pitch.mid",
        stem_output_dir / f"{stem_name}.mid",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate

    matches = sorted(stem_output_dir.rglob("*.mid"))
    stem_matches = [path for path in matches if stem_name in path.stem.lower()]
    if stem_matches:
        return stem_matches[0]
    if matches:
        return matches[0]

    raise FileNotFoundError(f"No MIDI output found for stem '{stem_name}' in {stem_output_dir}")


def _run_basic_pitch(wav_path: Path, output_dir: Path) -> None:
    """
    Run Basic Pitch in-process.

    The CLI subprocess with captured stdout/stderr can hang or exit without writing
    MIDI on macOS; calling predict_and_save directly is reliable.
    """
    if basic_pitch_predict_and_save is None or ICASSP_2022_MODEL_PATH is None:
        raise RuntimeError(
            "Basic Pitch is not installed. Run: cd backend && bash scripts/install_basic_pitch.sh"
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(
        "Running Basic Pitch in-process for %s -> %s (python=%s)",
        wav_path,
        output_dir,
        sys.executable,
    )
    basic_pitch_predict_and_save(
        [wav_path],
        output_dir,
        save_midi=True,
        sonify_midi=False,
        save_model_outputs=False,
        save_notes=False,
        model_or_model_path=ICASSP_2022_MODEL_PATH,
    )


def _transcribe_single_stem(stem_name: str, wav_path: Path, job_output_dir: Path) -> tuple[str, str | None]:
    """
    Transcribe one stem WAV to MIDI.

    Returns:
        Tuple of (stem_name, midi_path) on success.

    Raises:
        RuntimeError: If Basic Pitch fails or MIDI output is missing.
    """
    if not wav_path.is_file():
        raise RuntimeError(f"Stem WAV not found for '{stem_name}': {wav_path}")

    stem_output_dir = _resolve_stem_midi_dir(job_output_dir, stem_name)

    try:
        _run_basic_pitch(wav_path, stem_output_dir)
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(f"Failed to run Basic Pitch for '{stem_name}': {exc}") from exc

    try:
        midi_path = _find_midi_file(stem_output_dir, stem_name)
    except FileNotFoundError as exc:
        listing = sorted(str(path.relative_to(stem_output_dir)) for path in stem_output_dir.rglob("*"))
        files_hint = ", ".join(listing[:12]) if listing else "(no files written)"
        raise RuntimeError(
            f"Basic Pitch finished for '{stem_name}' but no MIDI was found in {stem_output_dir}. "
            f"Files there: {files_hint}. "
            f"Reinstall with backend/scripts/install_basic_pitch.sh if this persists."
        ) from exc

    return stem_name, str(midi_path)


def transcribe_stems(
    job_id: str,
    stem_paths: dict[str, str],
    output_dir: str | Path | None = None,
) -> TranscriptionResult:
    """
    Run Basic Pitch on vocals, other, and bass stems and return MIDI paths.

    Args:
        job_id: Upload job identifier used for output directory naming.
        stem_paths: Mapping of Demucs stem names to WAV file paths.
        output_dir: Optional override for the parent MIDI directory.

    Returns:
        TranscriptionResult with paths to each generated MIDI file.
    """
    job_output_dir = _resolve_midi_output_dir(job_id, Path(output_dir) if output_dir else None)
    warnings = [DRUMS_SKIPPED_WARNING]
    midi_paths: dict[str, str] = {}
    collected_stderr: list[str] = []

    missing_stems = [stem for stem in TRANSCRIPTION_STEMS if stem not in stem_paths]
    if missing_stems:
        return TranscriptionResult(
            success=False,
            job_id=job_id,
            output_dir=str(job_output_dir),
            warnings=warnings,
            error=f"Missing required stems for transcription: {', '.join(missing_stems)}",
        )

    try:
        for stem_name in TRANSCRIPTION_STEMS:
            wav_path = Path(stem_paths[stem_name])
            _, midi_path = _transcribe_single_stem(stem_name, wav_path, job_output_dir)
            midi_paths[stem_name] = midi_path
            logger.info("Transcribed stem '%s' for job_id=%s -> %s", stem_name, job_id, midi_path)
    except (RuntimeError, FileNotFoundError) as exc:
        logger.exception("Transcription failed for job_id=%s on stem batch", job_id)
        return TranscriptionResult(
            success=False,
            job_id=job_id,
            output_dir=str(job_output_dir),
            midi_paths=midi_paths,
            warnings=warnings,
            error=str(exc),
            stderr="\n".join(collected_stderr) or None,
        )

    return TranscriptionResult(
        success=True,
        job_id=job_id,
        output_dir=str(job_output_dir),
        midi_paths=midi_paths,
        warnings=warnings,
    )


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage: python -m app.pipeline.transcription "
            '<\'{"vocals":"/path/vocals.wav","other":"/path/other.wav","bass":"/path/bass.wav"}\'>'
        )

    payload = json.loads(sys.argv[1])
    job_id = payload.pop("job_id", "smoke-job")
    result = transcribe_stems(job_id, payload)
    print(result.model_dump_json(indent=2))
    if not result.success:
        raise SystemExit(1)
