# backend/tests/unit/test_notation.py

from pathlib import Path

import pytest
from music21 import note, stream

from app.config import get_settings
from app.pipeline.notation import (
    ALTO_MIN_MIDI,
    CLEANUP_WARNING,
    MELODY_FOCUS_WARNING,
    SOPRANO_MIN_MIDI,
    _assign_vocal_part,
    _dedupe_pitch_buckets,
    _filter_short_notes,
    build_satb_score,
    cleanup_midi_elements,
    merge_satb_parts,
    split_vocals_into_satb_parts,
    validate_musicxml,
)


def _write_simple_midi(path: Path, midi_values: list[int]) -> None:
    """Create a minimal monophonic MIDI file for tests."""
    part = stream.Part()
    for index, midi_value in enumerate(midi_values):
        part.insert(float(index), note.Note(midi_value, quarterLength=1.0))
    score = stream.Score()
    score.append(part)
    score.write("midi", fp=str(path))


def test_assign_vocal_part_splits_by_pitch_range() -> None:
    assert _assign_vocal_part(SOPRANO_MIN_MIDI) == "Soprano"
    assert _assign_vocal_part(SOPRANO_MIN_MIDI - 1) == "Alto"
    assert _assign_vocal_part(ALTO_MIN_MIDI) == "Alto"
    assert _assign_vocal_part(ALTO_MIN_MIDI - 1) is None


def test_split_vocals_into_satb_parts(tmp_path: Path) -> None:
    vocals_midi = tmp_path / "vocals.mid"
    _write_simple_midi(vocals_midi, [62, 57, 72])  # D4, A3, C5

    soprano, alto = split_vocals_into_satb_parts(vocals_midi)

    assert len(list(soprano.flatten().notes)) == 2
    assert len(list(alto.flatten().notes)) == 1


def test_merge_satb_parts_creates_four_parts() -> None:
    parts = [stream.Part(id=name) for name in ("Soprano", "Alto", "Tenor", "Bass")]
    score = merge_satb_parts(*parts)

    assert len(score.parts) == 4


def test_build_satb_score_validates_round_trip(tmp_path: Path) -> None:
    midi_paths = {}
    for stem_name, pitches in {
        "vocals": [64, 57],
        "other": [67],
        "bass": [48],
    }.items():
        midi_file = tmp_path / f"{stem_name}.mid"
        _write_simple_midi(midi_file, pitches)
        midi_paths[stem_name] = str(midi_file)

    result = build_satb_score("notation-unit-test", midi_paths)

    assert result.success is True
    assert result.music_xml is not None
    assert validate_musicxml(result.music_xml)
    assert "Soprano" in result.music_xml or "score-partwise" in result.music_xml


def test_validate_musicxml_rejects_empty_string() -> None:
    assert validate_musicxml("") is False


def test_filter_short_notes_removes_brief_detections() -> None:
    long_note = note.Note(60, quarterLength=0.5)
    short_note = note.Note(62, quarterLength=0.05)

    filtered = _filter_short_notes([long_note, short_note], min_quarter_length=0.125)

    assert len(filtered) == 1
    assert filtered[0].pitch.midi == 60


def test_dedupe_pitch_buckets_keeps_longest_duration() -> None:
    first = note.Note(60, quarterLength=0.25)
    first.offset = 0.0
    duplicate = note.Note(60, quarterLength=0.5)
    duplicate.offset = 0.02

    deduped = _dedupe_pitch_buckets([first, duplicate], grid_quarter_length=0.125)

    assert len(deduped) == 1
    assert deduped[0].quarterLength == 0.5


def test_melody_focus_produces_fewer_notes_than_dense_input() -> None:
    dense: list[note.Note] = []
    for step in range(32):
        for pitch in (60, 62, 64, 66, 68):
            dense.append(note.Note(pitch, quarterLength=0.125))
            dense[-1].offset = float(step) * 0.125

    strict = cleanup_midi_elements(dense, profile="soprano")
    assert len(strict) < len(dense)


def test_build_satb_score_includes_melody_focus_warning(tmp_path: Path) -> None:
    get_settings.cache_clear()
    midi_paths = {}
    for stem_name, pitches in {
        "vocals": [64, 57],
        "other": [67],
        "bass": [48],
    }.items():
        midi_file = tmp_path / f"{stem_name}.mid"
        _write_simple_midi(midi_file, pitches)
        midi_paths[stem_name] = str(midi_file)

    result = build_satb_score("melody-focus-test", midi_paths)

    assert result.success is True
    if get_settings().notation_melody_focus:
        assert MELODY_FOCUS_WARNING in result.warnings


def test_build_satb_score_includes_cleanup_warning(tmp_path: Path) -> None:
    midi_paths = {}
    for stem_name, pitches in {
        "vocals": [64, 57],
        "other": [67],
        "bass": [48],
    }.items():
        midi_file = tmp_path / f"{stem_name}.mid"
        _write_simple_midi(midi_file, pitches)
        midi_paths[stem_name] = str(midi_file)

    result = build_satb_score("cleanup-warning-test", midi_paths)

    assert result.success is True
    assert CLEANUP_WARNING in result.warnings
