# AI-assisted: Milestone 3 notation result models — merged SATB MusicXML output.

from pydantic import BaseModel, Field


class NotationResult(BaseModel):
    """Structured outcome from converting MIDI stems to SATB MusicXML."""

    success: bool
    job_id: str
    music_xml: str | None = None
    warnings: list[str] = Field(default_factory=list)
    error: str | None = None
