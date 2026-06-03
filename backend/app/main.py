# AI-assisted: ScoreFlow FastAPI app — upload pipeline, export, and optional AI completion.

import logging
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response

from app.config import get_settings
from app.models.job import JobRecord, JobStatus, JobStatusResponse, UploadResponse
from app.pipeline.orchestrator import process_upload_job
from app.routers import completion_routes, export_routes
from app.utils.audio_validation import validate_wav_upload
from app.utils.job_store import job_store
from app.utils.stem_files import resolve_job_stem_path

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Initialize runtime resources on startup."""
    settings = get_settings()
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.stems_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.midi_dir).mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title="ScoreFlow API", version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(export_routes.router)
app.include_router(completion_routes.router)


@app.get("/api/health")
def health_check() -> dict[str, str]:
    """Simple health probe."""
    return {"status": "ok"}


@app.post("/api/upload", response_model=UploadResponse)
async def upload_audio(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
) -> UploadResponse:
    """
    Accept a WAV upload, persist it, and return a job_id immediately.

    Processing continues asynchronously via a background task.
    """
    if file.filename is None:
        raise HTTPException(status_code=400, detail="Filename is required.")

    settings = get_settings()
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    header_bytes = await file.read(44)
    await file.seek(0)
    contents = await file.read()
    size_bytes = len(contents)

    validation = validate_wav_upload(
        filename=file.filename,
        content_type=file.content_type,
        size_bytes=size_bytes,
        max_size_bytes=settings.max_upload_size_bytes,
        header_bytes=header_bytes,
    )
    if not validation.is_valid:
        raise HTTPException(status_code=400, detail=validation.error)

    job_id = str(uuid.uuid4())
    destination = upload_dir / f"{job_id}.wav"

    try:
        destination.write_bytes(contents)
    except OSError as exc:
        logger.exception("Failed to write upload for job_id=%s", job_id)
        raise HTTPException(status_code=500, detail="Failed to store uploaded file.") from exc

    job_store.create(
        JobRecord(
            job_id=job_id,
            status=JobStatus.QUEUED,
            original_filename=file.filename,
            stored_path=str(destination),
            size_bytes=size_bytes,
        )
    )

    background_tasks.add_task(process_upload_job, job_id)

    return UploadResponse(
        job_id=job_id,
        status=JobStatus.QUEUED,
        message="Upload received. Processing will begin shortly.",
    )


@app.get("/api/jobs/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str) -> JobStatusResponse:
    """Return the current status of an upload/processing job."""
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job_store.to_status_response(job)


@app.get("/api/jobs/{job_id}/stems/{stem_name}")
def get_job_stem(job_id: str, stem_name: str, download: bool = False) -> FileResponse:
    """Stream or download a separated Demucs stem WAV for a completed job."""
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")

    stem_path = resolve_job_stem_path(job, stem_name)
    filename = f"{stem_name}.wav"

    return FileResponse(
        path=stem_path,
        media_type="audio/wav",
        filename=filename if download else None,
        content_disposition_type="attachment" if download else "inline",
    )


@app.get("/api/jobs/{job_id}/score")
def get_job_score(job_id: str) -> Response:
    """Return the merged SATB MusicXML for a completed job."""
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")

    if job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Job not completed yet.")

    if not job.music_xml:
        raise HTTPException(status_code=404, detail="Score not available for this job.")

    return Response(content=job.music_xml, media_type="application/xml")
