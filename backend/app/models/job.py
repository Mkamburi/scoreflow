# AI-assisted: Milestone 1 job models for async upload tracking.

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Lifecycle states for an upload job."""

    QUEUED = "queued"
    RECEIVED = "received"
    SEPARATING = "separating"
    TRANSCRIBING = "transcribing"
    NOTATING = "notating"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobRecord(BaseModel):
    """Internal job record stored by the job store."""

    job_id: str
    status: JobStatus
    original_filename: str
    stored_path: str
    size_bytes: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    error: str | None = None
    stems_dir: str | None = None
    demucs_stems: dict[str, str] | None = None
    satb_stems: dict[str, str | None] | None = None
    warnings: list[str] = Field(default_factory=list)
    midi_paths: dict[str, str] | None = None
    music_xml: str | None = None


class UploadResponse(BaseModel):
    """Response returned immediately after a successful upload."""

    job_id: str
    status: JobStatus
    message: str


class JobStatusResponse(BaseModel):
    """Public job status payload."""

    job_id: str
    status: JobStatus
    original_filename: str
    size_bytes: int
    created_at: datetime
    updated_at: datetime
    error: str | None = None
    stems_dir: str | None = None
    demucs_stems: dict[str, str] | None = None
    satb_stems: dict[str, str | None] | None = None
    warnings: list[str] = Field(default_factory=list)
    has_score: bool = False
