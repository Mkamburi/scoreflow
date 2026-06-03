# backend/tests/unit/test_completion.py

import tempfile
from pathlib import Path

from music21 import note, stream

from app.completion.suggest import suggest_harmony


def _satb_musicxml() -> str:
    soprano = stream.Part(id="Soprano")
    alto = stream.Part(id="Alto")
    tenor = stream.Part(id="Tenor")
    bass = stream.Part(id="Bass")

    soprano.insert(0, note.Note(64, quarterLength=1.0))
    bass.insert(0, note.Note(48, quarterLength=1.0))

    score = stream.Score()
    score.append(soprano)
    score.append(alto)
    score.append(tenor)
    score.append(bass)

    with tempfile.NamedTemporaryFile(suffix=".musicxml", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    score.write("musicxml", fp=str(tmp_path))
    xml = tmp_path.read_text(encoding="utf-8")
    tmp_path.unlink(missing_ok=True)
    return xml


def test_suggest_harmony_updates_bass_part() -> None:
    result_xml, warnings, error = suggest_harmony(_satb_musicxml(), target_part="Bass")

    assert error is None
    assert result_xml is not None
    assert len(warnings) > 0
    assert "Bass" in result_xml or "score-partwise" in result_xml
