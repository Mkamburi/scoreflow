# backend/tests/integration/test_score_endpoint.py

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.job import JobRecord, JobStatus
from app.utils.job_store import job_store


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_get_job_score_returns_musicxml(client: TestClient, tmp_path: Path) -> None:
    job_id = "score-endpoint-job"
    music_xml = '<?xml version="1.0"?><score-partwise version="3.1"><part-list/></score-partwise>'
    job_store.create(
        JobRecord(
            job_id=job_id,
            status=JobStatus.COMPLETED,
            original_filename="song.wav",
            stored_path=str(tmp_path / "song.wav"),
            size_bytes=100,
            music_xml=music_xml,
        )
    )

    response = client.get(f"/api/jobs/{job_id}/score")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/xml")
    assert "score-partwise" in response.text


def test_get_job_score_returns_400_when_not_completed(client: TestClient, tmp_path: Path) -> None:
    job_id = "score-in-progress-job"
    job_store.create(
        JobRecord(
            job_id=job_id,
            status=JobStatus.TRANSCRIBING,
            original_filename="song.wav",
            stored_path=str(tmp_path / "song.wav"),
            size_bytes=100,
        )
    )

    response = client.get(f"/api/jobs/{job_id}/score")

    assert response.status_code == 400


def test_get_job_score_returns_404_for_unknown_job(client: TestClient) -> None:
    response = client.get("/api/jobs/missing/score")

    assert response.status_code == 404
