# backend/tests/unit/test_export.py

from pathlib import Path

import pytest
from music21 import note, stream

from app.export.converters import ExportConversionError, musicxml_to_midi_bytes, parse_validated_score


def _minimal_musicxml() -> str:
    import tempfile
    from pathlib import Path

    part = stream.Part(id="Soprano")
    part.insert(0, note.Note(60, quarterLength=1.0))
    score = stream.Score()
    score.append(part)

    with tempfile.NamedTemporaryFile(suffix=".musicxml", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    score.write("musicxml", fp=str(tmp_path))
    xml = tmp_path.read_text(encoding="utf-8")
    tmp_path.unlink(missing_ok=True)
    return xml


def test_parse_validated_score_rejects_empty() -> None:
    with pytest.raises(ExportConversionError):
        parse_validated_score("")


def test_musicxml_to_midi_bytes_returns_non_empty_mid() -> None:
    midi_bytes = musicxml_to_midi_bytes(_minimal_musicxml())

    assert len(midi_bytes) > 0
    assert midi_bytes[:4] == b"MThd"
