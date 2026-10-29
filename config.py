from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the AI customer support agent."""

    # Application settings
    app_name: str = "AI Customer Support Agent"
    app_env: str = "development"
    debug: bool = False

    # LLM settings
    model_provider: str = "openrouter"
    model_name: str = "nvidia/nemotron-3.5-super-vl:free"
    model_temperature: float = Field(default=0.0, ge=0.0, le=2.0)

    # OpenRouter settings
    openrouter_api_key: str | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_site_url: str | None = None
    openrouter_app_name: str = "AI Customer Support Agent"

    # Other model providers
    google_api_key: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None

    # Web search
    tavily_api_key: str | None = None

    # LangSmith
    langsmith_tracing: bool = False
    langsmith_api_key: str | None = None
    langsmith_project: str = "ai-customer-support"

    # Storage
    database_path: str = "storage/support.db"
    vector_store_path: str = "storage/vector_store"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def validate_model_configuration(self) -> None:
        """Validate the selected provider and its API key."""

        provider_key_map = {
            "openrouter": self.openrouter_api_key,
            "google_genai": self.google_api_key,
            "openai": self.openai_api_key,
            "anthropic": self.anthropic_api_key,
        }

        provider = self.model_provider.lower()

        if provider not in provider_key_map:
            supported = ", ".join(provider_key_map)
            raise ValueError(
                f"Unsupported model provider: {provider}. "
                f"Supported providers: {supported}"
            )

        if not provider_key_map[provider]:
            env_key_map = {
                "openrouter": "OPENROUTER_API_KEY",
                "google_genai": "GOOGLE_API_KEY",
                "openai": "OPENAI_API_KEY",
                "anthropic": "ANTHROPIC_API_KEY",
            }

            raise ValueError(
                f"{env_key_map[provider]} is required "
                f"when using the '{provider}' provider."
            )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached settings instance."""
    return Settings()


settings = get_settings()