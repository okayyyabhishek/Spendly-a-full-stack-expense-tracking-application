"""Central application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed configuration; secrets are deliberately supplied only through the environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        # `frontend_origins` is deliberately a comma-separated environment
        # variable, not JSON. Let the field validator normalize it below.
        enable_decoding=False,
    )

    app_name: str = "Spendly API"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    # Support both common local development hostnames. Browsers treat
    # localhost and 127.0.0.1 as distinct origins for CORS purposes.
    frontend_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"]
    )
    database_url: str = "mysql+pymysql://expense_app:change-me-local@localhost:3306/expense_tracker"
    jwt_secret_key: str = "local-development-secret-change-before-deployment"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    recurring_processor_interval_minutes: int = 15

    @field_validator("frontend_origins", mode="before")
    @classmethod
    def parse_frontend_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
