# AI-assisted: Milestone 2 stem file serving — safe path resolution for Demucs outputs.

from pathlib import Path

from fastapi import HTTPException

from app.config import get_settings
from app.models.job import JobRecord

ALLOWED_DEMUCS_STEMS = frozenset({"vocals", "drums", "bass", "other"})


def resolve_job_stem_path(job: JobRecord, stem_name: str) -> Path:
    """
    Resolve and validate a Demucs stem path for a completed job.

    Ensures the stem name is allowed, the job has stems, and the file lives
    under the configured stems directory.
    """
    if stem_name not in ALLOWED_DEMUCS_STEMS:
        raise HTTPException(status_code=400, detail=f"Invalid stem name: {stem_name}")

    if not job.demucs_stems:
        raise HTTPException(status_code=404, detail="Stems are not available for this job yet.")

    stem_path_value = job.demucs_stems.get(stem_name)
    if not stem_path_value:
        raise HTTPException(status_code=404, detail=f"Stem not found: {stem_name}")

    stem_path = Path(stem_path_value).resolve()
    stems_root = Path(get_settings().stems_dir).resolve()

    if stems_root not in stem_path.parents and stem_path != stems_root:
        raise HTTPException(status_code=403, detail="Stem path is outside the allowed directory.")

    if not stem_path.is_file():
        raise HTTPException(status_code=404, detail=f"Stem file missing on disk: {stem_name}")

    return stem_path
