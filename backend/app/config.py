# AI-assisted: Milestone 1 upload scaffold — env-driven paths and limits per ScoreFlow spec.

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    upload_dir: str = "/tmp/scoreflow/uploads"
    stems_dir: str = "/tmp/scoreflow/stems"
    midi_dir: str = "/tmp/scoreflow/midi"
    max_upload_size_mb: int = 50
    pipeline_max_audio_seconds: float = 120
    separation_timeout_sec: int = 1800
    transcription_timeout_sec: int = 1800
    notation_min_note_quarter_length: float = 0.25
    notation_dedupe_grid_quarter_length: float = 0.5
    notation_max_notes_per_bar: int = 8
    notation_max_bars: int = 64
    notation_melody_focus: bool = True
    notation_melody_max_bars: int = 32
    notation_melody_min_velocity: int = 45
    enable_ai_completion: bool = False
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def max_upload_size_bytes(self) -> int:
        """Maximum upload size in bytes."""
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def cors_origin_list(self) -> list[str]:
        """Parsed CORS allowlist."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
