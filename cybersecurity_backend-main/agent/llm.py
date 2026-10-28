"""Groq LLM client wrapper.

Uses the Groq OpenAI-compatible chat completions API via `requests`
(already a project dependency). Exposes a single async `generate_text`
helper. All AI features must go through this module so that configuration,
error handling and unavailability are handled in one place.

Configuration (in .env):
- GROQ_API_KEY : Groq API key (required for AI features)
- GROQ_MODEL   : model ID (default: openai/gpt-oss-120b)
"""

import os
import asyncio
import logging
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_TIMEOUT = 120  # seconds


class LLMNotAvailableError(Exception):
    """Raised when the LLM is not configured or the API call fails."""
    pass


def _get_api_key() -> Optional[str]:
    key = GROQ_API_KEY.strip()
    if not key or key.startswith("your-"):
        return None
    return key


def llm_available() -> bool:
    """Return True if the LLM client is configured and ready."""
    return _get_api_key() is not None


async def generate_text(
    prompt: str,
    max_output_tokens: int = 4096,
    temperature: float = 0.4,
) -> str:
    """Generate text from a prompt. Raises LLMNotAvailableError on failure.

    The synchronous HTTP call is executed in a worker thread to avoid
    blocking the event loop.
    """
    api_key = _get_api_key()
    if api_key is None:
        raise LLMNotAvailableError("Groq API key not configured")

    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_output_tokens,
        "temperature": temperature,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    def _call():
        response = requests.post(
            GROQ_API_URL,
            json=payload,
            headers=headers,
            timeout=GROQ_TIMEOUT,
        )
        if response.status_code == 401:
            raise LLMNotAvailableError("Groq API key is invalid or revoked")
        if response.status_code == 404:
            raise LLMNotAvailableError(
                f"Groq model '{GROQ_MODEL}' not available. "
                "Set GROQ_MODEL in .env to a valid model ID."
            )
        if response.status_code == 429:
            raise LLMNotAvailableError("Groq rate limit exceeded, try again shortly")
        response.raise_for_status()
        return response.json()

    try:
        data = await asyncio.to_thread(_call)
    except LLMNotAvailableError:
        raise
    except Exception as e:
        raise LLMNotAvailableError(f"Groq API call failed: {e}")

    choices = data.get("choices") or []
    if not choices:
        raise LLMNotAvailableError("Groq returned no choices (content may have been blocked)")

    content = (choices[0].get("message") or {}).get("content")
    if not content:
        finish_reason = choices[0].get("finish_reason", "unknown")
        raise LLMNotAvailableError(f"Groq returned an empty response (finish_reason: {finish_reason})")

    return content
