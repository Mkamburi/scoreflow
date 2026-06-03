# AI-assisted: Milestone 3 transcription result models — Basic Pitch MIDI outputs per stem.

from pydantic import BaseModel, Field


class TranscriptionResult(BaseModel):
    """Structured outcome from transcribing separated stems to MIDI."""

    success: bool
    job_id: str
    output_dir: str | None = None
    midi_paths: dict[str, str] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    error: str | None = None
    stderr: str | None = None
