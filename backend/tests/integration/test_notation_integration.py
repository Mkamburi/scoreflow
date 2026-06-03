# backend/tests/integration/test_notation_integration.py

from pathlib import Path

import pytest

from app.pipeline.notation import build_satb_score, validate_musicxml

LOVESTAINED_MIDI_DIR = Path("/tmp/scoreflow/midi/lovestained-test")


@pytest.mark.skipif(
    not (LOVESTAINED_MIDI_DIR / "vocals" / "vocals_basic_pitch.mid").is_file(),
    reason="Run transcription on lovestained stems first",
)
def test_build_satb_score_from_lovestained_midis() -> None:
    """Round-trip integration test using real Basic Pitch MIDI outputs."""
    midi_paths = {
        "vocals": str(LOVESTAINED_MIDI_DIR / "vocals" / "vocals_basic_pitch.mid"),
        "other": str(LOVESTAINED_MIDI_DIR / "other" / "other_basic_pitch.mid"),
        "bass": str(LOVESTAINED_MIDI_DIR / "bass" / "bass_basic_pitch.mid"),
    }

    result = build_satb_score("lovestained-integration", midi_paths)

    assert result.success is True
    assert result.music_xml is not None
    assert validate_musicxml(result.music_xml)
    assert len(result.music_xml) > 500
