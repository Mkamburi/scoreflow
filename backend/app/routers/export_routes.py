# AI-assisted: Milestone 4 export API routes.

import re

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.export.converters import ExportConversionError, musicxml_to_midi_bytes, musicxml_to_pdf_bytes
from app.models.export import ExportRequest
from app.pipeline.notation import validate_musicxml

router = APIRouter(prefix="/api/export", tags=["export"])

_SAFE_NAME = re.compile(r"[^a-zA-Z0-9._-]+")


def _safe_filename(base: str, extension: str) -> str:
    cleaned = _SAFE_NAME.sub("_", base).strip("._") or "scoreflow-score"
    return f"{cleaned}.{extension}"


@router.post("/musicxml")
def export_musicxml(payload: ExportRequest) -> Response:
    """Validate and return MusicXML as a downloadable attachment."""
    if not validate_musicxml(payload.music_xml):
        raise HTTPException(status_code=400, detail="MusicXML failed validation.")

    filename = _safe_filename(payload.filename, "musicxml")
    return Response(
        content=payload.music_xml,
        media_type="application/vnd.recordare.musicxml+xml",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/midi")
def export_midi(payload: ExportRequest) -> Response:
    """Convert validated MusicXML to MIDI and return as a download."""
    try:
        midi_bytes = musicxml_to_midi_bytes(payload.music_xml)
    except ExportConversionError as exc:
        detail = {"detail": str(exc), "fallback": exc.fallback}
        raise HTTPException(status_code=400, detail=detail) from exc

    filename = _safe_filename(payload.filename, "mid")
    return Response(
        content=midi_bytes,
        media_type="audio/midi",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/pdf")
def export_pdf(payload: ExportRequest) -> Response:
    """Convert validated MusicXML to PDF via LilyPond when installed."""
    try:
        pdf_bytes = musicxml_to_pdf_bytes(payload.music_xml)
    except ExportConversionError as exc:
        detail = {"detail": str(exc), "fallback": exc.fallback}
        raise HTTPException(status_code=400, detail=detail) from exc

    filename = _safe_filename(payload.filename, "pdf")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
