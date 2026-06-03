# AI-assisted: Milestone 5 completion API — feature-flagged harmony suggestions.

from fastapi import APIRouter, HTTPException

from app.completion.suggest import suggest_harmony
from app.config import get_settings
from app.models.completion import CompletionRequest, CompletionResponse

router = APIRouter(prefix="/api/completion", tags=["completion"])


@router.get("/status")
def completion_status() -> dict[str, bool]:
    """Report whether AI completion endpoints are enabled."""
    settings = get_settings()
    return {"enabled": settings.enable_ai_completion}


@router.post("/suggest", response_model=CompletionResponse)
def completion_suggest(payload: CompletionRequest) -> CompletionResponse:
    """Suggest harmony in a target part from the current edited MusicXML."""
    settings = get_settings()
    if not settings.enable_ai_completion:
        raise HTTPException(
            status_code=403,
            detail="AI completion is disabled. Set ENABLE_AI_COMPLETION=true in backend .env.",
        )

    music_xml, warnings, error = suggest_harmony(
        payload.music_xml,
        target_part=payload.target_part,
        style=payload.style,
    )

    if error or not music_xml:
        return CompletionResponse(success=False, warnings=warnings, error=error or "Completion failed.")

    return CompletionResponse(success=True, music_xml=music_xml, warnings=warnings)
