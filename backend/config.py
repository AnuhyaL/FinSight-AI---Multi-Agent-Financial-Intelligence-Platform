from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"
    finbert_model: str = "ProsusAI/finbert"
    embedding_model: str = "all-MiniLM-L6-v2"
    cors_origins: str = "http://localhost:5173"
    max_upload_mb: int = 25
    chroma_dir: str = "./data/chroma"
    reports_dir: str = "./data/reports"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def resolved_reports_dir(self) -> Path:
        path = Path(self.reports_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
