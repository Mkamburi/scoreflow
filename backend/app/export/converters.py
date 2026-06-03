# AI-assisted: Milestone 4 export — validate MusicXML and convert to MIDI/PDF via music21.

import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

from music21 import converter

from app.pipeline.notation import validate_musicxml

logger = logging.getLogger(__name__)


class ExportConversionError(Exception):
    """Raised when MusicXML cannot be converted for export."""

    def __init__(self, message: str, *, fallback: str | None = None) -> None:
        super().__init__(message)
        self.fallback = fallback


def parse_validated_score(music_xml: str):
    """Parse MusicXML after validation; raises ExportConversionError on failure."""
    if not validate_musicxml(music_xml):
        raise ExportConversionError(
            "MusicXML failed validation. Fix notation errors before exporting.",
            fallback="Re-open the score in the editor and simplify dense passages.",
        )

    with tempfile.NamedTemporaryFile(suffix=".musicxml", delete=False) as tmp_file:
        tmp_path = Path(tmp_file.name)
        tmp_path.write_text(music_xml, encoding="utf-8")

    try:
        return converter.parse(str(tmp_path))
    except Exception as exc:
        logger.exception("MusicXML parse failed during export")
        raise ExportConversionError(f"Could not parse MusicXML: {exc}") from exc
    finally:
        tmp_path.unlink(missing_ok=True)


def musicxml_to_midi_bytes(music_xml: str) -> bytes:
    """Convert validated MusicXML to a MIDI file."""
    score = parse_validated_score(music_xml)

    with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as tmp_file:
        tmp_path = Path(tmp_file.name)

    try:
        score.write("midi", fp=str(tmp_path))
        return tmp_path.read_bytes()
    except Exception as exc:
        logger.exception("MIDI export failed")
        raise ExportConversionError(f"MIDI conversion failed: {exc}") from exc
    finally:
        tmp_path.unlink(missing_ok=True)


def musicxml_to_pdf_bytes(music_xml: str) -> bytes:
    """
    Convert MusicXML to PDF via LilyPond when available.

    MUSICAL NOTE: LilyPond produces publication-quality choral scores; without it
    we return a clear error so the client can fall back to browser print.
    """
    if not shutil.which("lilypond"):
        raise ExportConversionError(
            "LilyPond is not installed on the server.",
            fallback="Use “Print to PDF” in the browser export panel.",
        )

    score = parse_validated_score(music_xml)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        lily_path = tmp_path / "score.ly"
        pdf_path = tmp_path / "score.pdf"

        try:
            score.write("lilypond", fp=str(lily_path))
        except Exception as exc:
            logger.exception("LilyPond file generation failed")
            raise ExportConversionError(f"Could not prepare LilyPond source: {exc}") from exc

        result = subprocess.run(
            ["lilypond", "-o", str(tmp_path / "score"), str(lily_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0 or not pdf_path.is_file():
            logger.error("lilypond stderr: %s", result.stderr)
            raise ExportConversionError(
                "LilyPond failed to render PDF.",
                fallback="Use “Print to PDF” in the browser export panel.",
            )

        return pdf_path.read_bytes()
