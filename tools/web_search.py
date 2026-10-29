import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from langchain_core.tools import tool

from config import get_settings



@tool
def search_web(query: str) -> dict:
    """Search the public web for current information relevant to a customer support question."""

    # Validate the query FIRST.
    if not query or not query.strip():
        return {
            "ok": False,
            "error": "Search query cannot be empty.",
        }

    # Check configuration only after validating the query.
    settings = get_settings()
    api_key = settings.tavily_api_key

    if not api_key:
        return {
            "ok": False,
            "error": (
                "Web search is not configured. Add TAVILY_API_KEY "
                "to your .env file to enable it."
            ),
        }


    payload = json.dumps(
        {
            "api_key": api_key,
            "query": query.strip(),
            "max_results": 5,
            "search_depth": "basic",
        }
    ).encode("utf-8")

    request = Request(
        "https://api.tavily.com/search",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))

        results = [
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content": item.get("content", ""),
            }
            for item in data.get("results", [])
        ]

        return {
            "ok": True,
            "query": query,
            "results": results,
        }

    except HTTPError as exc:
        return {
            "ok": False,
            "error": f"Web search service returned HTTP {exc.code}.",
        }

    except (URLError, TimeoutError, json.JSONDecodeError):
        return {
            "ok": False,
            "error": "Web search failed. Please try again later.",
        }