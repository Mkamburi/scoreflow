# AI-assisted: Milestone 1 in-memory job store — swap for Redis/DB in production.

from datetime import datetime, timezone
from threading import Lock
from typing import Any

from app.models.job import JobRecord, JobStatus, JobStatusResponse


class JobStore:
    """Thread-safe in-memory job registry."""

    def __init__(self) -> None:
        self._jobs: dict[str, JobRecord] = {}
        self._lock = Lock()

    def create(self, job: JobRecord) -> JobRecord:
        """Persist a new job record."""
        with self._lock:
            self._jobs[job.job_id] = job
        return job

    def get(self, job_id: str) -> JobRecord | None:
        """Fetch a job by id."""
        with self._lock:
            return self._jobs.get(job_id)

    def update_status(self, job_id: str, status: JobStatus, error: str | None = None) -> JobRecord | None:
        """Update job status and optional error message."""
        return self.update_job(job_id, status=status, error=error)

    def update_job(self, job_id: str, **updates: Any) -> JobRecord | None:
        """Apply partial updates to a job record."""
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            updated = job.model_copy(
                update={
                    **updates,
                    "updated_at": datetime.now(timezone.utc),
                }
            )
            self._jobs[job_id] = updated
            return updated

    def to_status_response(self, job: JobRecord) -> JobStatusResponse:
        """Convert an internal record to an API response."""
        return JobStatusResponse(
            job_id=job.job_id,
            status=job.status,
            original_filename=job.original_filename,
            size_bytes=job.size_bytes,
            created_at=job.created_at,
            updated_at=job.updated_at,
            error=job.error,
            stems_dir=job.stems_dir,
            demucs_stems=job.demucs_stems,
            satb_stems=job.satb_stems,
            warnings=job.warnings,
            has_score=bool(job.music_xml),
        )


job_store = JobStore()
