from functools import lru_cache
from typing import List, Optional, Union
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application Metadata
    APP_NAME: str = "LinkSentry Backend"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    API_PREFIX: str = "/api"

    # ML Model Artifact Paths
    TEXT_MODEL_PATH: Optional[str] = None
    TEXT_VECTORIZER_PATH: Optional[str] = None
    URL_MODEL_PATH: Optional[str] = None

    # Risk Fusion Weights (Default: text 45%, url 35%, rules 20%)
    TEXT_WEIGHT: float = 0.45
    URL_WEIGHT: float = 0.35
    RULE_WEIGHT: float = 0.20

    # Input Constraints
    MAX_TEXT_LENGTH: int = 10000
    MAX_URL_LENGTH: int = 4096

    # Rate Limiting Configuration
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_ANALYZE: str = "60/minute"

    # CORS Configuration
    ALLOWED_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://localhost:8000",
    ]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return [str(i).strip() for i in v if str(i).strip()]
        return []

    @model_validator(mode="after")
    def validate_security_settings(self) -> "Settings":
        env = (self.ENVIRONMENT or "development").lower()
        origins = self.ALLOWED_ORIGINS

        if env == "production":
            if not origins:
                raise ValueError("ALLOWED_ORIGINS must be explicitly configured in production mode.")
            if "*" in origins:
                raise ValueError("Wildcard CORS origin '*' is strictly prohibited in production mode.")
            for origin in origins:
                if not (origin.startswith("http://") or origin.startswith("https://")):
                    raise ValueError(f"Invalid CORS origin scheme: '{origin}'. Origins must start with http:// or https://")
        else:
            if "*" in origins and len(origins) > 1:
                raise ValueError("Wildcard origin '*' cannot be combined with explicit origins in ALLOWED_ORIGINS.")

        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()

