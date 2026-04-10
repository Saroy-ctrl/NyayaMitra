"""
groq_client.py — Async Groq API wrapper for NyayaMitra.

Uses the groq Python SDK with model llama-3.3-70b-versatile.
Reads GROQ_API_KEY from environment (loaded by main.py via python-dotenv).
Retry logic: 3 attempts with exponential backoff, handling RateLimitError.
"""

import asyncio
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Client — lazily initialised on first call
# ---------------------------------------------------------------------------
_client = None


def get_client():
    """Return (or lazily create) the shared AsyncGroq client."""
    global _client
    if _client is None:
        from groq import AsyncGroq
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY environment variable is not set.")
        _client = AsyncGroq(api_key=api_key)
    return _client


# ---------------------------------------------------------------------------
# Primary helper — used by all 4 agents
# ---------------------------------------------------------------------------
MAX_RETRIES = 3
MODEL_LARGE = "llama-3.3-70b-versatile"   # drafter only — 100K TPD
MODEL_FAST  = "llama-3.1-8b-instant"      # all other agents — 500K TPD


async def call_groq(
    system_prompt: str,
    user_message: str,
    temperature: float = 0.3,
    max_tokens: int = 1024,
    model: str = MODEL_FAST,
) -> str:
    """
    Send a chat completion request to Groq and return the raw text response.

    Implements 3 retry attempts with exponential backoff (2^attempt seconds),
    specifically handling groq.RateLimitError. Other exceptions are re-raised
    immediately after all attempts are exhausted.

    Args:
        system_prompt: LLM system instructions.
        user_message:  User-turn content.
        temperature:   Sampling temperature (low = more deterministic JSON).
        max_tokens:    Upper bound on response length.

    Returns:
        The assistant's raw text response (usually JSON string for agents).

    Raises:
        groq.RateLimitError: If all retry attempts are exhausted due to rate limits.
        Exception: On non-rate-limit API failures after all retries.
    """
    from groq import RateLimitError

    client = get_client()

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_message},
    ]

    last_exception: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""

        except RateLimitError as exc:
            last_exception = exc
            if attempt < MAX_RETRIES:
                wait = 2 ** attempt  # 2s, 4s between attempts 1->2, 2->3
                logger.warning(
                    "Groq rate limit hit (attempt %d/%d). Retrying in %.0fs...",
                    attempt, MAX_RETRIES, wait,
                )
                await asyncio.sleep(wait)
            else:
                logger.error(
                    "Groq rate limit: all %d attempts exhausted.", MAX_RETRIES
                )

        except Exception as exc:
            last_exception = exc
            if attempt < MAX_RETRIES:
                wait = 2 ** attempt
                logger.warning(
                    "Groq API error (attempt %d/%d): %s. Retrying in %.0fs...",
                    attempt, MAX_RETRIES, exc, wait,
                )
                await asyncio.sleep(wait)
            else:
                logger.error(
                    "Groq API error: all %d attempts exhausted. Last error: %s",
                    MAX_RETRIES, exc,
                )

    # All retries exhausted — re-raise the last exception
    raise last_exception  # type: ignore[misc]
