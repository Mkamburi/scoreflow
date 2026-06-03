# AI-assisted: Milestone 5 completion — rule-based bass harmony from soprano melody.
# Optional OpenAI adapter when OPENAI_API_KEY is set. Core pipeline does not depend on this module.

import logging
import os
import tempfile
from pathlib import Path

from music21 import chord, converter, note, stream

from app.pipeline.notation import validate_musicxml

logger = logging.getLogger(__name__)

COMPLETION_WARNING = (
    "Harmony suggestions are algorithmic (root notes under the melody). "
    "Review and edit in Flat before exporting."
)


def _find_part(score: stream.Score, part_name: str) -> stream.Part | None:
    """Locate a part by id, part name, or standard SATB order."""
    target = part_name.lower()
    for part in score.parts:
        for label in (getattr(part, "partName", None), part.id):
            if label is not None and str(label).lower() == target:
                return part

    if len(score.parts) == 4:
        index_by_name = {"soprano": 0, "alto": 1, "tenor": 2, "bass": 3}
        index = index_by_name.get(target)
        if index is not None:
            return score.parts[index]

    return None


def _soprano_reference_part(score: stream.Score) -> stream.Part | None:
    """Prefer Soprano; fall back to the highest part with notes."""
    return _find_part(score, "Soprano") or (score.parts[0] if score.parts else None)


def _merge_simple_bass_harmony(score: stream.Score, target_part_name: str) -> stream.Score:
    """
    Add simple root notes in the bass under soprano melody notes.

    MUSICAL NOTE: This is a teaching/demo heuristic — one bass note per soprano onset,
    placed a fifth or octave below when possible, not a full harmonic analysis.
    """
    soprano = _soprano_reference_part(score)
    bass = _find_part(score, target_part_name)
    if soprano is None or bass is None:
        raise ValueError(f"Could not find Soprano and {target_part_name} parts in the score.")

    melody_notes = [
        element
        for element in soprano.flatten().notesAndRests
        if element.isNote or element.isChord
    ]
    if not melody_notes:
        raise ValueError("No melody notes found to seed harmony.")

    for element in list(bass.flatten().notesAndRests):
        bass.remove(element)

    for element in melody_notes:
        if isinstance(element, chord.Chord):
            pitch = element.pitches[0]
        else:
            pitch = element.pitch

        # MUSICAL NOTE: Prefer a fifth below; clamp to a reasonable choral bass range.
        bass_midi = max(36, min(60, pitch.midi - 7))
        bass_note = note.Note(bass_midi, quarterLength=element.quarterLength)
        bass.insert(element.offset, bass_note)

    return score


def _score_to_musicxml(score: stream.Score) -> str:
    """Serialize a music21 Score to MusicXML."""
    with tempfile.NamedTemporaryFile(suffix=".musicxml", delete=False) as tmp_file:
        tmp_path = Path(tmp_file.name)

    try:
        score.write("musicxml", fp=str(tmp_path))
        return tmp_path.read_text(encoding="utf-8")
    finally:
        tmp_path.unlink(missing_ok=True)


def suggest_harmony(
    music_xml: str,
    target_part: str = "Bass",
    style: str = "simple_roots",
) -> tuple[str | None, list[str], str | None]:
    """
    Return updated MusicXML with harmony suggestions merged into target_part.

    Uses OpenAI when OPENAI_API_KEY is set and style requests gpt; otherwise rule-based.
    """
    warnings = [COMPLETION_WARNING]

    if not validate_musicxml(music_xml):
        return None, warnings, "MusicXML failed validation."

    if style == "gpt" and os.environ.get("OPENAI_API_KEY"):
        gpt_result = _suggest_with_openai(music_xml, target_part)
        if gpt_result:
            return gpt_result, warnings, None
        warnings.append("GPT completion unavailable; used rule-based harmony instead.")

    try:
        with tempfile.NamedTemporaryFile(suffix=".musicxml", delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)
            tmp_path.write_text(music_xml, encoding="utf-8")

        score = converter.parse(str(tmp_path))
        tmp_path.unlink(missing_ok=True)

        if not hasattr(score, "parts"):
            return None, warnings, "Score has no parts to complete."

        updated = _merge_simple_bass_harmony(score, target_part)
        result_xml = _score_to_musicxml(updated)

        if not validate_musicxml(result_xml):
            return None, warnings, "Generated MusicXML failed validation."

        return result_xml, warnings, None
    except Exception as exc:
        logger.exception("Harmony suggestion failed")
        return None, warnings, str(exc)


def _suggest_with_openai(music_xml: str, target_part: str) -> str | None:
    """
    Optional GPT-4o adapter for harmony suggestions.

    Returns None when the openai package or API call fails so callers can fall back.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None

    try:
        from openai import OpenAI  # type: ignore[import-untyped]
    except ImportError:
        logger.warning("openai package not installed; skipping GPT completion")
        return None

    client = OpenAI(api_key=api_key)
    prompt = (
        f"You are a choral arranger. Given this MusicXML, suggest {target_part} harmony "
        "as valid MusicXML for the full SATB score. Return only MusicXML, no commentary.\n\n"
        f"{music_xml[:12000]}"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )
        text = response.choices[0].message.content
        if text and validate_musicxml(text):
            return text
    except Exception:
        logger.exception("OpenAI completion request failed")

    return None
