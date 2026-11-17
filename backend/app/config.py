from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

# Project root directory (d:\job-searching-engine)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    """Application configuration loaded from environment variables or .env file."""
    model_config = SettingsConfigDict(
        env_file=(BASE_DIR / ".env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    DATABASE_URL: str = Field(
        default="postgresql://user:password@localhost:5432/job_matching",
        description="PostgreSQL connection string with pgvector support"
    )
    GEMINI_API_KEY: str = Field(
        default="",
        description="Google Gemini API key from Google AI Studio"
    )
    GEMINI_MODEL: str = Field(
        default="gemini-2.5-flash",
        description="Gemini generative model for parsing and explanations"
    )
    EMBED_MODEL: str = Field(
        default="gemini-embedding-001",
        description="Gemini embedding model name"
    )
    EMBED_DIM: int = Field(
        default=768,
        description="Dimensionality of the dense embedding vectors"
    )

# Instantiate global settings
settings = Settings()

# Export EMBED_DIM as a standalone constant for database schemas & checks
EMBED_DIM: int = settings.EMBED_DIM
