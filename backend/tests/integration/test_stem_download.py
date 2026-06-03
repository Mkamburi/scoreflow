# backend/tests/integration/test_stem_download.py

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.job import JobRecord, JobStatus
from app.utils.job_store import job_store


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    stems_dir = tmp_path / "stems"
    stems_dir.mkdir()
    monkeypatch.setenv("STEMS_DIR", str(stems_dir))
    from app.config import get_settings

    get_settings.cache_clear()
    return TestClient(app)


def test_get_job_stem_streams_wav(client: TestClient, tmp_path: Path) -> None:
    job_id = "stem-stream-job"
    stem_path = tmp_path / "stems" / job_id / "htdemucs" / "track" / "vocals.wav"
    stem_path.parent.mkdir(parents=True)
    stem_path.write_bytes(b"RIFF" + b"\x00" * 44)

    job_store.create(
        JobRecord(
            job_id=job_id,
            status=JobStatus.COMPLETED,
            original_filename="track.wav",
            stored_path=str(tmp_path / "track.wav"),
            size_bytes=1024,
            demucs_stems={"vocals": str(stem_path)},
        )
    )

    response = client.get(f"/api/jobs/{job_id}/stems/vocals")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("audio/wav")
    assert response.content.startswith(b"RIFF")


def test_get_job_stem_returns_404_for_unknown_job(client: TestClient) -> None:
    response = client.get("/api/jobs/missing/stems/vocals")

    assert response.status_code == 404


def test_get_job_stem_rejects_invalid_stem_name(client: TestClient, tmp_path: Path) -> None:
    job_id = "invalid-stem-job"
    job_store.create(
        JobRecord(
            job_id=job_id,
            status=JobStatus.COMPLETED,
            original_filename="track.wav",
            stored_path=str(tmp_path / "track.wav"),
            size_bytes=1024,
            demucs_stems={"vocals": str(tmp_path / "vocals.wav")},
        )
    )

    response = client.get(f"/api/jobs/{job_id}/stems/not-a-stem")

    assert response.status_code == 400
