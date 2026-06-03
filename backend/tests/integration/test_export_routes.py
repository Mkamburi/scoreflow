# backend/tests/integration/test_export_routes.py

import pytest
from fastapi.testclient import TestClient
from music21 import note, stream

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


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


def test_export_musicxml_download(client: TestClient) -> None:
    payload = {"music_xml": _minimal_musicxml(), "filename": "demo-song"}

    response = client.post("/api/export/musicxml", json=payload)

    assert response.status_code == 200
    assert "score-partwise" in response.text
    assert "attachment" in response.headers.get("content-disposition", "")


def test_export_midi_download(client: TestClient) -> None:
    payload = {"music_xml": _minimal_musicxml(), "filename": "demo-song"}

    response = client.post("/api/export/midi", json=payload)

    assert response.status_code == 200
    assert response.content[:4] == b"MThd"


def test_export_musicxml_rejects_invalid(client: TestClient) -> None:
    response = client.post("/api/export/musicxml", json={"music_xml": "not-xml", "filename": "x"})

    assert response.status_code == 400


def test_completion_status_disabled_by_default(client: TestClient) -> None:
    response = client.get("/api/completion/status")

    assert response.status_code == 200
    assert response.json()["enabled"] is False


def test_completion_suggest_returns_403_when_disabled(client: TestClient) -> None:
    response = client.post(
        "/api/completion/suggest",
        json={"music_xml": _minimal_musicxml(), "target_part": "Bass"},
    )

    assert response.status_code == 403
