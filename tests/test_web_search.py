from types import SimpleNamespace
from unittest.mock import patch

from tools.web_search import search_web


@patch(
    "tools.web_search.get_settings",
    return_value=SimpleNamespace(tavily_api_key=None),
)
def test_web_search_without_api_key(mock_settings):
    result = search_web.invoke({"query": "shipping policy"})

    assert result["ok"] is False
    assert "TAVILY_API_KEY" in result["error"]


@patch(
    "tools.web_search.get_settings",
    return_value=SimpleNamespace(tavily_api_key=None),
)
def test_web_search_rejects_empty_query(mock_settings):
    result = search_web.invoke({"query": "   "})

    assert result["ok"] is False
    assert "empty" in result["error"].lower()