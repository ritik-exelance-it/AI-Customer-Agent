from unittest.mock import patch

from config import Settings
from model import get_chat_model


def test_openrouter_timeout_is_converted_from_seconds_to_milliseconds():
    settings = Settings(
        model_provider="openrouter",
        model_name="test/model",
        model_timeout_seconds=12.5,
        model_max_retries=0,
        openrouter_api_key="test-key",
    )

    with patch("model.ChatOpenRouter") as mock_chat_model:
        get_chat_model(settings)

    assert mock_chat_model.call_args.kwargs["timeout"] == 12_500
    assert mock_chat_model.call_args.kwargs["max_retries"] == 0
