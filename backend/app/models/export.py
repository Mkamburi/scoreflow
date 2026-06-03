# AI-assisted: Milestone 4 export models.

from pydantic import BaseModel, Field


class ExportRequest(BaseModel):
    """Client-submitted edited MusicXML for export."""

    music_xml: str = Field(..., min_length=1)
    filename: str = Field(default="scoreflow-score", max_length=120)


class ExportErrorResponse(BaseModel):
    """Structured export failure."""

    detail: str
    fallback: str | None = None
