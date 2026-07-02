"""
Groq LLM provider — Phase 4.1

Implements the ``LLMProvider`` protocol and the concrete ``GroqLLMProvider``
that calls the Groq chat-completions API with JSON-mode enforced.

Protocol
--------
Any object that satisfies ``LLMProvider`` can be passed to the recommender,
making it trivial to swap in ``MockLLMProvider`` for tests.
"""
from __future__ import annotations

import logging
import time
from typing import List, Protocol, runtime_checkable

from src.config import GROQ_API_KEY, GROQ_MODEL

logger = logging.getLogger(__name__)


# ── Protocol ──────────────────────────────────────────────────────────────────

@runtime_checkable
class LLMProvider(Protocol):
    """
    Minimal interface every LLM backend must satisfy.

    Parameters
    ----------
    messages : List[dict]
        Standard OpenAI-style message list:
        ``[{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]``

    Returns
    -------
    str
        Raw text content of the model's reply (the full JSON string when
        ``response_format`` is ``json_object``).
    """

    def complete(self, messages: List[dict]) -> str:
        ...


# ── Concrete Groq implementation ──────────────────────────────────────────────

class GroqLLMProvider:
    """
    Calls the Groq chat-completions endpoint and returns the raw content string.

    Parameters
    ----------
    api_key : str | None
        Groq API key.  Falls back to ``GROQ_API_KEY`` from config.
    model : str | None
        Groq model identifier.  Falls back to ``GROQ_MODEL`` from config.
    max_retries : int
        Number of times to retry on ``429 Too Many Requests`` before raising.
    retry_delay : float
        Initial back-off delay in seconds (doubles on each retry).
    temperature : float
        Sampling temperature (low value = more deterministic / consistent JSON).
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        max_retries: int = 3,
        retry_delay: float = 2.0,
        temperature: float = 0.3,
    ) -> None:
        self._api_key = api_key or GROQ_API_KEY
        self._model = model or GROQ_MODEL
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._temperature = temperature

        if not self._api_key:
            raise ValueError(
                "GROQ_API_KEY is not set. "
                "Add it to your .env file or pass it explicitly."
            )

        # Import lazily so the module can be imported without groq installed
        # (e.g. during test collection with mocks only).
        try:
            from groq import Groq  # type: ignore
            self._client = Groq(api_key=self._api_key)
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "The 'groq' package is required. Install it with: pip install groq"
            ) from exc

    # ── Public interface ──────────────────────────────────────────────────────

    def complete(self, messages: List[dict]) -> str:
        """
        Send *messages* to Groq and return the model's reply as a raw string.

        Retries up to ``max_retries`` times on HTTP 429 (rate-limit) responses,
        with exponential back-off.  All other errors are re-raised immediately.

        Parameters
        ----------
        messages : List[dict]
            ``[{"role": "system/user", "content": "..."}, ...]``

        Returns
        -------
        str
            The ``content`` field of the first choice's message.

        Raises
        ------
        groq.RateLimitError
            If all retries are exhausted.
        groq.APIError
            On any other API-level error.
        """
        from groq import RateLimitError  # type: ignore

        delay = self._retry_delay
        last_exc: Exception | None = None

        for attempt in range(1, self._max_retries + 1):
            try:
                logger.debug(
                    "[groq] Attempt %d/%d — model=%s",
                    attempt,
                    self._max_retries,
                    self._model,
                )
                response = self._client.chat.completions.create(
                    model=self._model,
                    messages=messages,  # type: ignore[arg-type]
                    response_format={"type": "json_object"},
                    temperature=self._temperature,
                )
                content: str = response.choices[0].message.content or ""
                logger.debug(
                    "[groq] Success — tokens used: %s",
                    getattr(response.usage, "total_tokens", "?"),
                )
                return content

            except RateLimitError as exc:
                last_exc = exc
                if attempt < self._max_retries:
                    logger.warning(
                        "[groq] Rate limit hit (attempt %d/%d). "
                        "Retrying in %.1fs …",
                        attempt,
                        self._max_retries,
                        delay,
                    )
                    time.sleep(delay)
                    delay *= 2  # exponential back-off
                else:
                    logger.error("[groq] Rate limit — all retries exhausted.")

        raise last_exc  # type: ignore[misc]
