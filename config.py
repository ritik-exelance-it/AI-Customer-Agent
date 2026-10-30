"""Application configuration loaded from environment variables or .env."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent


class Settings(BaseSettings):
    """Centralized settings for the AI customer support application."""

    app_name: str = "AI Customer Support Agent"
    app_env: str = "development"
    debug: bool = False

    model_provider: str = "openrouter"
    model_name: str = "nvidia/nemotron-3.5-super-vl:free"
    model_temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    model_timeout_seconds: float = Field(default=45.0, gt=0)
    model_max_retries: int = Field(default=0, ge=0, le=10)

    openrouter_api_key: str | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_site_url: str | None = None
    openrouter_app_name: str = "AI Customer Support Agent"

    google_api_key: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    tavily_api_key: str | None = None

    langsmith_tracing: bool = Field(default=False, validation_alias="LANGSMITH_TRACING")
    langsmith_api_key: str | None = Field(default=None, validation_alias="LANGSMITH_API_KEY")
    langsmith_project: str = Field(default="ai-customer-support", validation_alias="LANGSMITH_PROJECT")
    langsmith_endpoint: str = Field(default="https://api.smith.langchain.com", validation_alias="LANGSMITH_ENDPOINT")

    database_path: str = str(PROJECT_ROOT / "storage" / "support.db")
    vector_store_path: str = str(PROJECT_ROOT / "storage" / "vector_store")
    checkpoint_path: str = str(PROJECT_ROOT / "storage" / "checkpoints.sqlite")

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_ignore_empty=True,
    )

    def validate_model_configuration(self) -> None:
        """Raise a helpful error if the selected provider or key is invalid."""
        provider = self.model_provider.strip().lower()
        key_by_provider = {
            "openrouter": self.openrouter_api_key,
            "google_genai": self.google_api_key,
            "openai": self.openai_api_key,
            "anthropic": self.anthropic_api_key,
        }
        if provider not in key_by_provider:
            raise ValueError(
                f"Unsupported model provider '{provider}'. Supported providers: "
                f"{', '.join(key_by_provider)}."
            )
        if not key_by_provider[provider]:
            env_names = {
                "openrouter": "OPENROUTER_API_KEY",
                "google_genai": "GOOGLE_API_KEY",
                "openai": "OPENAI_API_KEY",
                "anthropic": "ANTHROPIC_API_KEY",
            }
            raise ValueError(
                f"{env_names[provider]} is required when MODEL_PROVIDER='{provider}'."
            )

    def get_provider_api_key(self) -> str:
        """Return the API key for the configured model provider."""
        self.validate_model_configuration()
        keys = {
            "openrouter": self.openrouter_api_key,
            "google_genai": self.google_api_key,
            "openai": self.openai_api_key,
            "anthropic": self.anthropic_api_key,
        }
        return keys[self.model_provider.strip().lower()]  # type: ignore[return-value]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return one cached settings instance."""
    return Settings()


# Compatibility alias for existing code importing `settings`.
settings = get_settings()
