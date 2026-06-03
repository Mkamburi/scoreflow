# AI-assisted: Milestone 5 completion models.

from pydantic import BaseModel, Field


class CompletionRequest(BaseModel):
    """Request harmony or bass suggestions from an edited score."""

    music_xml: str = Field(..., min_length=1)
    target_part: str = Field(default="Bass", description="Part id to fill (e.g. Bass, Tenor)")
    style: str = Field(default="simple_roots", max_length=40)


class CompletionResponse(BaseModel):
    """Updated MusicXML with suggested notes merged into the target part."""

    success: bool
    music_xml: str | None = None
    warnings: list[str] = Field(default_factory=list)
    error: str | None = None
