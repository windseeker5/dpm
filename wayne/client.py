"""Minimal OpenRouter client used only to select a Wayne skill.

OpenRouter never receives the database schema, query results, or permission to
write SQL. Configuration comes exclusively from the application's .env file.
"""

import os

import requests
from dotenv import load_dotenv


class OpenRouterConfigError(RuntimeError):
    pass


class OpenRouterRequestError(RuntimeError):
    pass


def _refresh_env() -> None:
    """Reload .env so debug-mode configuration changes work immediately."""
    load_dotenv(override=True)


def configured_model() -> str:
    _refresh_env()
    return os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-v4-flash").strip()


def select_skill(messages: list[dict], timeout: int = 30) -> dict:
    _refresh_env()
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")
    model = configured_model()

    if not api_key:
        raise OpenRouterConfigError("OPENROUTER_API_KEY is not configured in .env.")
    if not model:
        raise OpenRouterConfigError("OPENROUTER_MODEL is not configured in .env.")

    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://minipass.me",
                "X-Title": "minipass Wayne",
            },
            json={
                "model": model,
                "messages": messages,
                "temperature": 0,
                "max_tokens": 180,
                "response_format": {"type": "json_object"},
            },
            timeout=timeout,
        )
    except requests.RequestException as exc:
        raise OpenRouterRequestError(f"OpenRouter could not be reached: {exc}") from exc

    if response.status_code != 200:
        raise OpenRouterRequestError(
            f"OpenRouter returned HTTP {response.status_code}: {response.text[:300]}"
        )

    try:
        payload = response.json()
        return {
            "content": payload["choices"][0]["message"]["content"],
            "model": payload.get("model", model),
            "tokens_used": int(payload.get("usage", {}).get("total_tokens", 0) or 0),
        }
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise OpenRouterRequestError("OpenRouter returned an unexpected response.") from exc
