# AI-assisted: Milestone 2 separation result models — structured Demucs output for the pipeline.

from pydantic import BaseModel, Field


class SeparationResult(BaseModel):
    """Structured outcome from running htdemucs source separation."""

    success: bool
    job_id: str
    input_path: str
    output_dir: str | None = None
    model_name: str = "htdemucs"
    demucs_stems: dict[str, str] = Field(default_factory=dict)
    satb_stems: dict[str, str | None] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    error: str | None = None
    stderr: str | None = None
