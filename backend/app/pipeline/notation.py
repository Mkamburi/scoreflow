# AI-assisted: Milestone 3 notation — MIDI to SATB MusicXML via music21 with pitch-range vocal split.
# Includes MIDI cleanup: filter short notes, dedupe, quantize, and optional bar trim.

import logging
import re
import tempfile
from copy import deepcopy
from pathlib import Path
from dataclasses import dataclass
from typing import Literal

from music21 import chord, clef, converter, meter, note, stream

from app.config import get_settings
from app.models.notation import NotationResult

logger = logging.getLogger(__name__)

# MUSICAL NOTE: SATB pitch-range heuristics for splitting the shared vocals stem.
# Soprano: C4 (60) – G5 (79). Alto: G3 (55) – D5 (74).
# Overlap C4–D5 exists in both ranges; we assign C4 and above to soprano.
SOPRANO_MIN_MIDI = 60   # C4
SOPRANO_MAX_MIDI = 79   # G5
ALTO_MIN_MIDI = 55      # G3
ALTO_MAX_MIDI = 74      # D5

VOCAL_SPLIT_WARNING = (
    "Vocals were split into Soprano/Alto by pitch (C4+ → Soprano, G3–B3 → Alto). "
    "Overlapping notes in the C4–D5 zone are assigned to Soprano."
)

CLEANUP_WARNING = (
    "Transcription was simplified for readability (eighth-note grid, merged repeated "
    "pitches, dense passages thinned). It is a draft score — not a polished arrangement."
)

MELODY_FOCUS_WARNING = (
    "Melody-focus mode is on: score trimmed to the first 32 bars, quarter/half-note rhythm, "
    "sparse notes per bar (melody lines emphasized, bass simplified). Export is for sketching, "
    "not final engraving."
)

PartProfile = Literal["soprano", "alto", "tenor", "bass"]


@dataclass(frozen=True)
class CleanupParams:
    """Per-part MIDI cleanup tuning."""

    min_note_quarter_length: float
    dedupe_grid_quarter_length: float
    max_notes_per_bar: int
    min_velocity: int
    legato_gap: float
    quantize_grid: tuple[int, ...]
    round_durations: bool

SCORE_PART_IDS = {
    "Soprano": "P1",
    "Alto": "P2",
    "Tenor": "P3",
    "Bass": "P4",
}
PART_ORDER = ("Soprano", "Alto", "Tenor", "Bass")


def _note_velocity(element: note.Note | chord.Chord) -> int:
    """Return MIDI velocity (0–127); default mid-level when missing."""
    volume = getattr(element, "volume", None)
    if volume is not None and volume.velocity is not None:
        return int(volume.velocity)
    return 64


def _effective_max_bars() -> int:
    """Bar limit for export; melody-focus uses a shorter default."""
    settings = get_settings()
    if settings.notation_melody_focus and settings.notation_melody_max_bars > 0:
        return settings.notation_melody_max_bars
    return settings.notation_max_bars


def _cleanup_params_for(profile: PartProfile) -> CleanupParams:
    """Resolve cleanup strictness — melody-focus favors readable melodic lines."""
    settings = get_settings()
    if settings.notation_melody_focus:
        melody_profiles: dict[PartProfile, CleanupParams] = {
            "soprano": CleanupParams(0.5, 1.0, 4, 55, 1.0, (2, 4), True),
            "alto": CleanupParams(0.5, 1.0, 3, 50, 1.0, (2, 4), True),
            "tenor": CleanupParams(0.5, 0.5, 4, 45, 0.5, (4, 8), True),
            "bass": CleanupParams(0.5, 1.0, 2, 40, 1.0, (2, 4), True),
        }
        return melody_profiles[profile]

    return CleanupParams(
        min_note_quarter_length=settings.notation_min_note_quarter_length,
        dedupe_grid_quarter_length=settings.notation_dedupe_grid_quarter_length,
        max_notes_per_bar=settings.notation_max_notes_per_bar,
        min_velocity=0,
        legato_gap=settings.notation_dedupe_grid_quarter_length,
        quantize_grid=(4, 8),
        round_durations=False,
    )


def _midi_pitch_value(element: note.Note | chord.Chord) -> float:
    """Return the average MIDI pitch for a note or chord."""
    if isinstance(element, chord.Chord):
        pitches = [pitch.midi for pitch in element.pitches]
    else:
        pitches = [element.pitch.midi]
    return sum(pitches) / len(pitches)


def _assign_vocal_part(avg_midi: float) -> str | None:
    """
    Assign a vocal note to Soprano or Alto based on pitch range.

    Returns None for notes outside both choral ranges (likely transcription noise).
    """
    if SOPRANO_MIN_MIDI <= avg_midi <= SOPRANO_MAX_MIDI:
        return "Soprano"
    if ALTO_MIN_MIDI <= avg_midi < SOPRANO_MIN_MIDI:
        return "Alto"
    if avg_midi > SOPRANO_MAX_MIDI:
        # MUSICAL NOTE: Very high detections stay on Soprano rather than being dropped.
        return "Soprano"
    if ALTO_MIN_MIDI <= avg_midi <= ALTO_MAX_MIDI:
        return "Alto"
    return None


def _notes_from_stream(source: stream.Stream) -> list[note.Note | chord.Chord]:
    """Extract note and chord elements from a flattened stream."""
    return [
        element
        for element in source.flatten().notesAndRests
        if element.isNote or element.isChord
    ]


def _filter_short_notes(
    elements: list[note.Note | chord.Chord],
    min_quarter_length: float,
) -> list[note.Note | chord.Chord]:
    """
    Drop very short detections that Basic Pitch often emits as noise.

    MUSICAL NOTE: Sub-sixteenth fragments rarely represent intentional notation.
    """
    return [element for element in elements if element.quarterLength >= min_quarter_length]


def _dedupe_pitch_buckets(
    elements: list[note.Note | chord.Chord],
    grid_quarter_length: float,
) -> list[note.Note | chord.Chord]:
    """
    Merge duplicate pitch detections that land in the same rhythmic bucket.

    MUSICAL NOTE: Basic Pitch frequently emits stacked same-pitch blips; keeping
    the longest duration in each bucket reduces visual clutter on the staff.
    """
    merged: dict[tuple[float, int], note.Note | chord.Chord] = {}

    for element in sorted(elements, key=lambda item: item.offset):
        bucket = round(element.offset / grid_quarter_length) * grid_quarter_length
        pitch_key = int(round(_midi_pitch_value(element)))
        key = (bucket, pitch_key)

        if key not in merged:
            merged[key] = deepcopy(element)
            merged[key].offset = bucket
            continue

        existing = merged[key]
        existing.quarterLength = max(existing.quarterLength, element.quarterLength)

    return sorted(merged.values(), key=lambda item: item.offset)


def _quantize_elements(
    elements: list[note.Note | chord.Chord],
    grid: list[int] | None = None,
) -> list[note.Note | chord.Chord]:
    """
    Snap note starts and durations to a rhythmic grid using music21.

    Default grid uses eighth and sixteenth notes for readable notation.
    """
    if not elements:
        return []

    quantized_stream = stream.Part()
    for element in elements:
        quantized_stream.insert(element.offset, deepcopy(element))

    # Quarter + eighth only — sixteenth grid creates slash-like beam clutter in viewers.
    quantize_grid = grid or [4, 8]
    try:
        quantized_stream.quantize(
            quantize_grid,
            processOffsets=True,
            processDurations=True,
            inPlace=True,
        )
    except Exception:
        logger.warning("music21 quantize failed; returning deduped notes without quantization")
        return elements

    return _notes_from_stream(quantized_stream)


def _trim_elements_to_max_bars(
    elements: list[note.Note | chord.Chord],
    max_bars: int,
) -> list[note.Note | chord.Chord]:
    """Limit notation length for demo readability when max_bars > 0."""
    if max_bars <= 0:
        return elements

    max_offset = float(max_bars * 4)
    return [element for element in elements if element.offset < max_offset]


def _merge_legato_notes(
    elements: list[note.Note | chord.Chord],
    max_gap: float,
) -> list[note.Note | chord.Chord]:
    """Merge same-pitch notes separated by a small gap into one longer note."""
    if not elements:
        return []

    sorted_elements = sorted(elements, key=lambda item: float(item.offset))
    merged: list[note.Note | chord.Chord] = []

    for element in sorted_elements:
        pitch = int(round(_midi_pitch_value(element)))
        start = float(element.offset)
        end = start + float(element.quarterLength)

        if (
            merged
            and int(round(_midi_pitch_value(merged[-1]))) == pitch
            and start - (float(merged[-1].offset) + float(merged[-1].quarterLength)) <= max_gap
        ):
            existing = merged[-1]
            existing.quarterLength = max(float(existing.quarterLength), end - float(existing.offset))
            continue

        copy = deepcopy(element)
        copy.offset = start
        copy.quarterLength = end - start
        merged.append(copy)

    return merged


def _filter_low_velocity(
    elements: list[note.Note | chord.Chord],
    min_velocity: int,
) -> list[note.Note | chord.Chord]:
    """Drop quiet detections when min_velocity > 0."""
    if min_velocity <= 0:
        return elements
    return [element for element in elements if _note_velocity(element) >= min_velocity]


def _thin_dense_bars(
    elements: list[note.Note | chord.Chord],
    max_notes_per_bar: int,
    *,
    prefer_loudest: bool = False,
) -> list[note.Note | chord.Chord]:
    """Keep the strongest notes when Basic Pitch floods a bar with detections."""
    if max_notes_per_bar <= 0:
        return elements

    by_bar: dict[int, list[note.Note | chord.Chord]] = {}
    for element in elements:
        bar_index = int(float(element.offset) // 4)
        by_bar.setdefault(bar_index, []).append(element)

    thinned: list[note.Note | chord.Chord] = []
    for bar_notes in by_bar.values():
        if len(bar_notes) <= max_notes_per_bar:
            thinned.extend(bar_notes)
            continue

        if prefer_loudest:
            ranked = sorted(
                bar_notes,
                key=lambda item: (_note_velocity(item) * float(item.quarterLength), float(item.offset)),
                reverse=True,
            )
            kept = ranked[:max_notes_per_bar]
            thinned.extend(sorted(kept, key=lambda item: float(item.offset)))
            continue

        ordered = sorted(bar_notes, key=lambda item: float(item.offset))
        step = max(1, len(ordered) // max_notes_per_bar)
        thinned.extend(ordered[::step][:max_notes_per_bar])

    return sorted(thinned, key=lambda item: float(item.offset))


def _round_durations_to_beat_grid(
    elements: list[note.Note | chord.Chord],
    allowed_lengths: tuple[float, ...] = (0.5, 1.0, 2.0, 4.0),
) -> list[note.Note | chord.Chord]:
    """Snap note lengths to half / quarter / whole for cleaner notation."""
    rounded: list[note.Note | chord.Chord] = []
    for element in elements:
        copy = deepcopy(element)
        length = float(copy.quarterLength)
        copy.quarterLength = min(allowed_lengths, key=lambda value: abs(value - length))
        rounded.append(copy)
    return rounded


def cleanup_midi_elements(
    elements: list[note.Note | chord.Chord],
    profile: PartProfile = "tenor",
) -> list[note.Note | chord.Chord]:
    """Apply the full MIDI cleanup pipeline to a list of note/chord elements."""
    params = _cleanup_params_for(profile)
    cleaned = _filter_short_notes(elements, params.min_note_quarter_length)
    cleaned = _filter_low_velocity(cleaned, params.min_velocity)
    cleaned = _dedupe_pitch_buckets(cleaned, params.dedupe_grid_quarter_length)
    cleaned = _merge_legato_notes(cleaned, max_gap=params.legato_gap)
    cleaned = _quantize_elements(cleaned, list(params.quantize_grid))
    cleaned = _thin_dense_bars(
        cleaned,
        params.max_notes_per_bar,
        prefer_loudest=get_settings().notation_melody_focus,
    )
    if params.round_durations:
        cleaned = _round_durations_to_beat_grid(cleaned)
    cleaned = _trim_elements_to_max_bars(cleaned, _effective_max_bars())
    return cleaned


def _collapse_to_monophonic(
    elements: list[note.Note | chord.Chord],
    *,
    prefer: Literal["highest", "lowest"] = "highest",
) -> list[note.Note]:
    """Keep one note per onset — stacked MIDI pitches become a single readable line."""
    by_offset: dict[float, note.Note] = {}

    for element in sorted(elements, key=lambda item: float(item.offset)):
        offset = round(float(element.offset), 4)
        if element.isChord:
            midi_values = [pitch.midi for pitch in element.pitches]
            midi_value = max(midi_values) if prefer == "highest" else min(midi_values)
            candidate = note.Note(midi_value, quarterLength=element.quarterLength)
        elif element.isNote:
            candidate = deepcopy(element)
        else:
            continue

        candidate.offset = offset
        if offset not in by_offset:
            by_offset[offset] = candidate
            continue

        existing = by_offset[offset]
        if prefer == "lowest":
            if candidate.pitch.midi < existing.pitch.midi:
                by_offset[offset] = candidate
        elif candidate.pitch.midi > existing.pitch.midi:
            by_offset[offset] = candidate

    return sorted(by_offset.values(), key=lambda item: float(item.offset))


def _elements_to_part(
    elements: list[note.Note | chord.Chord],
    part_name: str,
    clef_obj: clef.Clef,
    *,
    prefer: Literal["highest", "lowest"] = "highest",
) -> stream.Part:
    """Build an unmeasured Part — measures are created once on the full score."""
    part = stream.Part(id=SCORE_PART_IDS.get(part_name, part_name))
    part.partName = part_name
    part.insert(0, clef_obj)
    for element in _collapse_to_monophonic(elements, prefer=prefer):
        part.insert(float(element.offset), element)
    return part


def _load_and_clean_midi(
    midi_path: str | Path,
    profile: PartProfile = "tenor",
) -> list[note.Note | chord.Chord]:
    """Parse a MIDI file and return cleaned note/chord elements."""
    parsed = converter.parse(str(midi_path))
    return cleanup_midi_elements(_notes_from_stream(parsed), profile=profile)


def split_vocals_into_satb_parts(vocals_midi_path: str | Path) -> tuple[stream.Part, stream.Part]:
    """
    Split vocals MIDI into Soprano and Alto parts by pitch range.

    Args:
        vocals_midi_path: Path to the vocals stem MIDI file.

    Returns:
        Tuple of (soprano_part, alto_part).
    """
    parsed = converter.parse(str(vocals_midi_path))
    raw_elements = _notes_from_stream(parsed)
    soprano_elements: list[note.Note | chord.Chord] = []
    alto_elements: list[note.Note | chord.Chord] = []

    for element in raw_elements:
        avg_midi = _midi_pitch_value(element)
        target = _assign_vocal_part(avg_midi)
        if target == "Soprano":
            soprano_elements.append(element)
        elif target == "Alto":
            alto_elements.append(element)

    soprano_part = _elements_to_part(
        cleanup_midi_elements(soprano_elements, profile="soprano"),
        "Soprano",
        clef.TrebleClef(),
        prefer="highest",
    )
    alto_part = _elements_to_part(
        cleanup_midi_elements(alto_elements, profile="alto"),
        "Alto",
        clef.TrebleClef(),
        prefer="highest",
    )
    return soprano_part, alto_part


def _midi_to_named_part(
    midi_path: str | Path,
    part_name: str,
    clef_obj: clef.Clef,
    *,
    profile: PartProfile = "tenor",
    prefer: Literal["highest", "lowest"] = "highest",
) -> stream.Part:
    """Convert a MIDI file into a named music21 Part with profile-specific cleanup."""
    parsed = converter.parse(str(midi_path))
    cleaned_elements = cleanup_midi_elements(_notes_from_stream(parsed), profile=profile)
    return _elements_to_part(cleaned_elements, part_name, clef_obj, prefer=prefer)


def merge_satb_parts(
    soprano: stream.Part,
    alto: stream.Part,
    tenor: stream.Part,
    bass: stream.Part,
) -> stream.Score:
    """Merge four parts into a single SATB Score with shared meter."""
    score = stream.Score(id="SATB")
    score.insert(0, meter.TimeSignature("4/4"))
    for part in (soprano, alto, tenor, bass):
        score.append(part)
    return score


def _finalize_score_for_export(score: stream.Score) -> stream.Score:
    """
    Create aligned 4/4 measures once on the combined score.

    Parts must arrive unmeasured; running makeMeasures twice corrupts offsets (garbled OSMD).
    """
    try:
        measured = score.makeMeasures(inPlace=False)
        if measured is not None:
            score = measured
        for part, name in zip(score.parts, PART_ORDER, strict=False):
            try:
                part.makeNotation(inPlace=True)
            except Exception:
                logger.warning("makeNotation failed for part %s", name)
            stable_id = SCORE_PART_IDS.get(name)
            if stable_id:
                part.id = stable_id
                part.partName = name
    except Exception:
        logger.exception("Score finalize failed; exporting best-effort MusicXML")
    return score


def _sanitize_musicxml_for_viewers(music_xml: str) -> str:
    """Patch music21 output for Flat.io and OSMD."""
    sanitized = re.sub(r"<!DOCTYPE[^>]*>\s*", "", music_xml)
    sanitized = sanitized.replace('version="4.0"', 'version="3.1"')
    sanitized = sanitized.replace("MusicXML 4.0", "MusicXML 3.1")
    sanitized = re.sub(r'\s+dynamics="[^"]*"', "", sanitized)
    sanitized = re.sub(r'\s+print-object="no"', "", sanitized)
    sanitized = re.sub(r"\s*<sound\s*/>\s*", "", sanitized)
    sanitized = re.sub(r"<tremolo[^>]*>.*?</tremolo>\s*", "", sanitized, flags=re.DOTALL)

    def _clamp_beats(match: re.Match[str]) -> str:
        beats = int(match.group(1))
        if beats < 1 or beats > 32:
            return "<beats>4</beats>"
        return match.group(0)

    sanitized = re.sub(r"<beats>(\d+)</beats>", _clamp_beats, sanitized)

    part_ids = re.findall(r'<score-part id="([^"]+)"', sanitized)
    for index, old_id in enumerate(part_ids, start=1):
        new_id = f"P{index}"
        if old_id == new_id:
            continue
        sanitized = sanitized.replace(f'<score-part id="{old_id}"', f'<score-part id="{new_id}"')
        sanitized = sanitized.replace(f'<part id="{old_id}"', f'<part id="{new_id}"')
    return sanitized


def _score_to_musicxml(score: stream.Score) -> str:
    """Serialize a music21 Score to viewer-friendly MusicXML 3.1."""
    export_score = _finalize_score_for_export(score)

    with tempfile.NamedTemporaryFile(suffix=".musicxml", delete=False) as tmp_file:
        tmp_path = Path(tmp_file.name)

    try:
        export_score.write("musicxml", fp=str(tmp_path))
        return _sanitize_musicxml_for_viewers(tmp_path.read_text(encoding="utf-8"))
    finally:
        tmp_path.unlink(missing_ok=True)


def validate_musicxml(music_xml: str) -> bool:
    """
    Validate that MusicXML parses cleanly in music21.

    Returns True when parse succeeds and at least one part is present.
    """
    if not music_xml.strip():
        return False

    with tempfile.NamedTemporaryFile(suffix=".musicxml", delete=False) as tmp_file:
        tmp_path = Path(tmp_file.name)
        tmp_path.write_text(music_xml, encoding="utf-8")

    try:
        parsed = converter.parse(str(tmp_path))
        parts = parsed.parts if hasattr(parsed, "parts") else [parsed]
        return len(parts) > 0
    except Exception:
        logger.exception("MusicXML validation failed")
        return False
    finally:
        tmp_path.unlink(missing_ok=True)


def build_satb_score(
    job_id: str,
    midi_paths: dict[str, str],
) -> NotationResult:
    """
    Convert transcription MIDIs to a merged, validated SATB MusicXML score.

    Args:
        job_id: Upload job identifier for logging.
        midi_paths: Mapping with keys vocals, other, bass → MIDI file paths.

    Returns:
        NotationResult containing validated MusicXML on success.
    """
    settings = get_settings()
    warnings = [VOCAL_SPLIT_WARNING, CLEANUP_WARNING]
    if settings.notation_melody_focus:
        warnings.append(MELODY_FOCUS_WARNING)
    max_bars = _effective_max_bars()
    if max_bars > 0:
        warnings.append(f"Score trimmed to the first {max_bars} bars for readability.")

    required = ("vocals", "other", "bass")
    missing = [stem for stem in required if stem not in midi_paths]
    if missing:
        return NotationResult(
            success=False,
            job_id=job_id,
            warnings=warnings,
            error=f"Missing MIDI paths for notation: {', '.join(missing)}",
        )

    try:
        for stem_name in required:
            if not Path(midi_paths[stem_name]).is_file():
                return NotationResult(
                    success=False,
                    job_id=job_id,
                    warnings=warnings,
                    error=f"MIDI file not found for '{stem_name}': {midi_paths[stem_name]}",
                )

        soprano_part, alto_part = split_vocals_into_satb_parts(midi_paths["vocals"])
        # MUSICAL NOTE: The "other" Demucs stem is our best proxy for Tenor in SATB layout.
        tenor_part = _midi_to_named_part(
            midi_paths["other"],
            "Tenor",
            clef.TrebleClef(),
            profile="tenor",
            prefer="highest",
        )
        bass_part = _midi_to_named_part(
            midi_paths["bass"],
            "Bass",
            clef.BassClef(),
            profile="bass",
            prefer="lowest",
        )

        score = merge_satb_parts(soprano_part, alto_part, tenor_part, bass_part)
        music_xml = _score_to_musicxml(score)

        if not validate_musicxml(music_xml):
            return NotationResult(
                success=False,
                job_id=job_id,
                warnings=warnings,
                error="Merged MusicXML failed validation.",
            )

        logger.info(
            "Notation complete for job_id=%s (music_xml_chars=%s)",
            job_id,
            len(music_xml),
        )
        return NotationResult(
            success=True,
            job_id=job_id,
            music_xml=music_xml,
            warnings=warnings,
        )
    except Exception as exc:
        logger.exception("Notation failed for job_id=%s", job_id)
        return NotationResult(
            success=False,
            job_id=job_id,
            warnings=warnings,
            error=f"Notation failed: {exc}",
        )


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage: python -m app.pipeline.notation "
            '<\'{"job_id":"x","vocals":"...","other":"...","bass":"..."}\'>'
        )

    payload = json.loads(sys.argv[1])
    job_id = payload.pop("job_id", "smoke-job")
    result = build_satb_score(job_id, payload)
    if result.success:
        print(f"MusicXML length: {len(result.music_xml or '')} chars")
    else:
        print(result.model_dump_json(indent=2))
        raise SystemExit(1)
