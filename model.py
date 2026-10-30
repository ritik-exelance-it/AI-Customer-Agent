"""Lazy model factory; importing this module does not require an API key."""

from functools import lru_cache
from typing import Any

from langchain.chat_models import init_chat_model
from langchain_openrouter import ChatOpenRouter

from config import Settings, get_settings


def get_chat_model(settings: Settings | None = None) -> Any:
    """Create a chat model using the supplied or cached settings."""
    settings = settings or get_settings()
    provider = settings.model_provider.strip().lower()
    api_key = settings.get_provider_api_key()

    if provider == "openrouter":
        return ChatOpenRouter(
            model=settings.model_name,
            api_key=api_key,
            temperature=settings.model_temperature,
            base_url=settings.openrouter_base_url,
            timeout=round(settings.model_timeout_seconds * 1_000),
            max_retries=settings.model_max_retries,
        )

    provider_names = {
        "google_genai": "google_genai",
        "openai": "openai",
        "anthropic": "anthropic",
    }
    if provider not in provider_names:
        raise ValueError(f"Unsupported model provider: {provider}")

    return init_chat_model(
        model=settings.model_name,
        model_provider=provider_names[provider],
        api_key=api_key,
        temperature=settings.model_temperature,
        timeout=settings.model_timeout_seconds,
        max_retries=settings.model_max_retries,
    )


@lru_cache(maxsize=1)
def get_cached_chat_model() -> Any:
    """Create and cache the default model after configuration is validated."""
    return get_chat_model()


class LazyChatModel:
    """Proxy that creates the actual model only when first used."""

    def __getattr__(self, name: str) -> Any:
        return getattr(get_cached_chat_model(), name)


# Existing imports such as `from model import llm` continue to work.
llm = LazyChatModel()
