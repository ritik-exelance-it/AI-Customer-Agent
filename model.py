from functools import lru_cache

from langchain_openrouter import ChatOpenRouter
from langchain.chat_models import init_chat_model

from config import Settings, get_settings


def get_chat_model(settings: Settings | None = None):
    if settings is None:
        settings = get_settings()

    provider = settings.model_provider.lower()

    if provider == "openrouter":
        api_key = settings.openrouter_api_key

        if not api_key:
            raise ValueError(
                "OpenRouter API key is missing. "
                "Set OPENROUTER_API_KEY in your .env file."
            )

        return ChatOpenRouter(
            model=settings.model_name,
            api_key=api_key,
            temperature=settings.model_temperature,
        )

    settings.validate_model_configuration()

    provider_map = {
        "google_genai": "google_genai",
        "openai": "openai",
        "anthropic": "anthropic",
    }

    if provider not in provider_map:
        raise ValueError(f"Unsupported model provider: {provider}")

    return init_chat_model(
        model=settings.model_name,
        model_provider=provider_map[provider],
        temperature=settings.model_temperature,
    )


@lru_cache(maxsize=1)
def get_cached_chat_model():
    return get_chat_model()


llm = get_cached_chat_model()