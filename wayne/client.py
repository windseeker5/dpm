"""Minimal OpenRouter client used only to select a Wayne skill.

OpenRouter never receives the database schema, query results, or permission to
write SQL. Configuration comes exclusively from the application's .env file.
"""

import os
import threading
from datetime import date

import requests
from dotenv import load_dotenv


class OpenRouterConfigError(RuntimeError):
    pass


class OpenRouterRequestError(RuntimeError):
    pass


class OpenRouterLimitError(OpenRouterRequestError):
    pass


class _RetryableResponseError(OpenRouterRequestError):
    pass


_quota_lock = threading.Lock()
_quota_day = date.today()
_quota_requests = 0


def _refresh_env() -> None:
    """Reload .env so debug-mode configuration changes work immediately."""
    load_dotenv(override=True)


def configured_model() -> str:
    _refresh_env()
    return os.getenv("OPENROUTER_MODEL", "openai/gpt-4.1-nano").strip()


def _claim_request() -> None:
    """Apply a per-process daily safety limit before making a paid request."""
    global _quota_day, _quota_requests
    try:
        daily_limit = max(0, int(os.getenv("OPENROUTER_DAILY_REQUEST_LIMIT", "50")))
    except ValueError as exc:
        raise OpenRouterConfigError("OPENROUTER_DAILY_REQUEST_LIMIT must be an integer.") from exc

    today = date.today()
    with _quota_lock:
        if today != _quota_day:
            _quota_day = today
            _quota_requests = 0
        if daily_limit == 0 or _quota_requests >= daily_limit:
            raise OpenRouterLimitError("Wayne's daily OpenRouter request limit has been reached.")
        _quota_requests += 1


def _parse_response(response, model: str) -> dict:
    try:
        payload = response.json()
        choice = payload["choices"][0]
        message = choice["message"]
        content = message.get("content")
        tokens_used = int(payload.get("usage", {}).get("total_tokens", 0) or 0)
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise _RetryableResponseError("OpenRouter returned an unexpected response.") from exc

    if not isinstance(content, str) or not content.strip():
        raise _RetryableResponseError("OpenRouter returned an empty response.")
    if choice.get("finish_reason") == "length":
        raise _RetryableResponseError("OpenRouter returned a truncated response.")

    return {
        "content": content,
        "model": payload.get("model", model),
        "tokens_used": tokens_used,
    }


def select_skill(messages: list[dict], timeout: int = 12) -> dict:
    _refresh_env()
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")
    model = configured_model()

    if not api_key:
        raise OpenRouterConfigError("OPENROUTER_API_KEY is not configured in .env.")
    if not model:
        raise OpenRouterConfigError("OPENROUTER_MODEL is not configured in .env.")

    try:
        max_tokens = max(100, min(800, int(os.getenv("OPENROUTER_MAX_TOKENS", "300"))))
    except ValueError as exc:
        raise OpenRouterConfigError("OPENROUTER_MAX_TOKENS must be an integer.") from exc

    last_error = None
    for attempt in range(2):
        _claim_request()
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
                    "max_tokens": max_tokens,
                    "response_format": {"type": "json_object"},
                    "reasoning": {"effort": "minimal", "exclude": True},
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
            return _parse_response(response, model)
        except _RetryableResponseError as exc:
            last_error = exc
            if attempt == 0:
                continue

    raise last_error or OpenRouterRequestError("OpenRouter did not return a usable response.")
