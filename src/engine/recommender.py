"""
Recommender orchestrator — Phase 4.3

Wires the full recommendation pipeline:

    UserPreferences
        → filter_restaurants()          (Phase 3.1 — filter engine)
        → format_candidates()           (Phase 3.2 — formatter)
        → build_messages()              (Phase 3.3 — prompt builder)
        → LLMProvider.complete()        (Phase 4.1 — Groq provider)
        → parse_groq_response()         (Phase 4.2 — parser)
        → RecommendationResult

The ``LLMProvider`` is injectable so tests can pass a ``MockLLMProvider``
without touching the network.
"""
from __future__ import annotations

import logging
from typing import List, Optional

from src.config import validate_config
from src.data.schema import Restaurant, RecommendationResult
from src.engine.groq_provider import GroqLLMProvider, LLMProvider
from src.engine.parser import parse_groq_response
from src.integration.filter import filter_restaurants
from src.integration.formatter import format_candidates
from src.integration.prompt_builder import build_messages
from src.input.preferences import UserPreferences

logger = logging.getLogger(__name__)


def get_recommendations(
    prefs: UserPreferences,
    catalog: List[Restaurant],
    *,
    llm_provider: Optional[LLMProvider] = None,
) -> RecommendationResult:
    """
    Run the full recommendation pipeline and return ranked results.

    Parameters
    ----------
    prefs : UserPreferences
        Validated user preferences from Phase 2.
    catalog : List[Restaurant]
        The full preprocessed restaurant catalog from Phase 1.
    llm_provider : LLMProvider | None
        Optional override for the LLM backend.  Defaults to
        ``GroqLLMProvider()`` (reads ``GROQ_API_KEY`` / ``GROQ_MODEL`` from
        config).  Pass a ``MockLLMProvider`` in tests.

    Returns
    -------
    RecommendationResult
        Always returns a result.  On Groq failure the parser's fallback is
        used so callers always get *something* to display.

    Raises
    ------
    ValueError
        If ``GROQ_API_KEY`` is missing and no custom provider was supplied.
    RuntimeError
        If the filtered candidate list is empty even after full relaxation.
    """
    # ── 0. Validate config (fast-fail if key is missing) ─────────────────────
    if llm_provider is None:
        if not validate_config():
            raise ValueError(
                "GROQ_API_KEY is not configured. "
                "Set it in your .env file before calling get_recommendations()."
            )
        llm_provider = GroqLLMProvider()

    # ── 1. Filter catalog ─────────────────────────────────────────────────────
    logger.info(
        "[recommender] Filtering catalog (%d restaurants) for location='%s', "
        "budget='%s', cuisine='%s', min_rating=%s",
        len(catalog),
        prefs.location,
        prefs.budget.value,
        prefs.cuisine or "any",
        prefs.min_rating,
    )
    candidates, filters_relaxed = filter_restaurants(catalog, prefs)
    logger.info(
        "[recommender] %d candidates after filtering (relaxed: %s)",
        len(candidates),
        filters_relaxed or "none",
    )

    if not candidates:
        raise RuntimeError(
            f"No restaurants found for location='{prefs.location}'. "
            "Check that this location exists in the dataset."
        )

    # ── 2. Serialise candidates for the prompt ────────────────────────────────
    candidates_json = format_candidates(candidates)

    # ── 3. Build messages ─────────────────────────────────────────────────────
    messages = build_messages(prefs, candidates_json, filters_relaxed)

    # ── 4. Call LLM ───────────────────────────────────────────────────────────
    logger.info(
        "[recommender] Sending %d candidates to LLM (%s) …",
        len(candidates),
        type(llm_provider).__name__,
    )
    try:
        raw_response = llm_provider.complete(messages)
    except Exception as exc:
        logger.error("[recommender] LLM call failed: %s", exc)
        # Parse with empty raw so the parser will fall back to top-N
        raw_response = ""

    # ── 5. Parse response ─────────────────────────────────────────────────────
    result = parse_groq_response(
        raw_response,
        candidates=candidates,
        filters_relaxed=filters_relaxed,
        llm_provider=llm_provider,
        messages=messages,
    )

    logger.info(
        "[recommender] Done — %d recommendations returned.",
        len(result.recommendations),
    )
    return result
