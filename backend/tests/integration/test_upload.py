# backend/tests/integration/test_upload.py

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.job import JobStatus
from tests.conftest import make_test_wav


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    monkeypatch.setenv("UPLOAD_DIR", str(upload_dir))
    monkeypatch.setenv("MAX_UPLOAD_SIZE_MB", "50")

    from app.config import get_settings

    get_settings.cache_clear()
    return TestClient(app)


def test_upload_returns_job_id_for_valid_wav(client: TestClient) -> None:
    wav_bytes = make_test_wav(duration_sec=0.25)

    response = client.post(
        "/api/upload",
        files={"file": ("test_mono.wav", wav_bytes, "audio/wav")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["job_id"]
    assert payload["status"] == JobStatus.QUEUED.value

    status_response = client.get(f"/api/jobs/{payload['job_id']}")
    assert status_response.status_code == 200
    status_payload = status_response.json()
    assert status_payload["original_filename"] == "test_mono.wav"
    assert status_payload["size_bytes"] == len(wav_bytes)


def test_upload_rejects_invalid_extension(client: TestClient) -> None:
    response = client.post(
        "/api/upload",
        files={"file": ("bad.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 400
    assert "Only .wav files are supported." in response.json()["detail"]


def test_get_job_status_returns_404_for_unknown_job(client: TestClient) -> None:
    response = client.get("/api/jobs/does-not-exist")

    assert response.status_code == 404
