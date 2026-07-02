"""
Response parser — Phase 4.2

Parses Groq's raw JSON string into a typed ``RecommendationResult``.

Fallback strategy
-----------------
If the JSON is malformed or fails schema validation:
  1. A single retry is attempted with a ``fix your JSON`` follow-up prompt
     (when an ``LLMProvider`` is supplied).
  2. If the retry also fails (or no provider is given), the top-N candidates
     are returned with a generic explanation so the user always gets a result.
"""
from __future__ import annotations

import json
import logging
from typing import Dict, List, Optional, TYPE_CHECKING

from src.data.schema import Recommendation, RecommendationResult, Restaurant
from src.config import TOP_N

if TYPE_CHECKING:
    from src.engine.groq_provider import LLMProvider

logger = logging.getLogger(__name__)

# ── Helpers ───────────────────────────────────────────────────────────────────

_FIX_JSON_PROMPT = (
    "Your previous response was not valid JSON or did not match the required schema. "
    "Please respond ONLY with valid JSON matching this exact schema:\n"
    "{\n"
    '  "summary": "string or null",\n'
    '  "recommendations": [\n'
    '    {"restaurant_id": "string", "rank": 1, "explanation": "string"}\n'
    "  ]\n"
    "}\n"
    "Do not include any text outside the JSON object."
)


def _build_candidate_index(candidates: List[Restaurant]) -> Dict[str, Restaurant]:
    """Return a dict keyed by restaurant id for O(1) lookup."""
    return {r.id: r for r in candidates}


def _parse_raw(raw: str) -> dict:
    """
    Attempt to parse *raw* as JSON.  Raises ``ValueError`` on failure.
    """
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON decode error: {exc}") from exc


def _validate_schema(data: dict) -> None:
    """
    Validate that *data* contains the required top-level keys and that each
    recommendation entry has ``restaurant_id``, ``rank``, and ``explanation``.

    Raises ``ValueError`` with a descriptive message on failure.
    """
    if "recommendations" not in data:
        raise ValueError("Missing key 'recommendations' in Groq response.")
    if not isinstance(data["recommendations"], list):
        raise ValueError("'recommendations' must be a list.")
    for i, rec in enumerate(data["recommendations"]):
        for key in ("restaurant_id", "rank", "explanation"):
            if key not in rec:
                raise ValueError(
                    f"Recommendation[{i}] missing key '{key}'."
                )


def _map_recommendations(
    data: dict,
    index: Dict[str, Restaurant],
    candidates: List[Restaurant],
) -> List[Recommendation]:
    """
    Map parsed recommendation entries to ``Recommendation`` objects.

    Unknown ``restaurant_id`` values are skipped with a warning; the caller
    gets however many valid mappings are produced (may be fewer than 5).
    """
    result: List[Recommendation] = []
    for entry in data["recommendations"]:
        rid = entry["restaurant_id"]
        restaurant = index.get(rid)
        if restaurant is None:
            logger.warning(
                "[parser] restaurant_id '%s' not found in candidate list — skipping.",
                rid,
            )
            continue
        result.append(
            Recommendation(
                restaurant=restaurant,
                rank=int(entry["rank"]),
                explanation=str(entry["explanation"]),
            )
        )
    # Sort by rank just in case the model returned them out-of-order
    result.sort(key=lambda r: r.rank)
    return result


def _fallback_result(
    candidates: List[Restaurant],
    top_n: int = TOP_N,
) -> RecommendationResult:
    """
    Build a ``RecommendationResult`` from the top-``top_n`` candidates using a
    generic explanation.  Used when parsing/retry both fail.
    """
    logger.warning(
        "[parser] Using fallback recommendations (top %d candidates).", top_n
    )
    recs = [
        Recommendation(
            restaurant=r,
            rank=i + 1,
            explanation=(
                "This restaurant was selected based on your location, budget, "
                "and rating preferences."
            ),
        )
        for i, r in enumerate(candidates[:top_n])
    ]
    return RecommendationResult(
        recommendations=recs,
        summary=(
            "AI ranking was unavailable; showing top candidates by filter match."
        ),
        filters_relaxed=[],
    )


# ── Public API ────────────────────────────────────────────────────────────────

def parse_groq_response(
    raw: str,
    candidates: List[Restaurant],
    filters_relaxed: Optional[List[str]] = None,
    *,
    llm_provider: Optional["LLMProvider"] = None,
    messages: Optional[List[dict]] = None,
) -> RecommendationResult:
    """
    Parse Groq's raw JSON string into a ``RecommendationResult``.

    Parameters
    ----------
    raw : str
        The raw string returned by ``LLMProvider.complete()``.
    candidates : List[Restaurant]
        The filtered candidate list whose IDs the model should have used.
    filters_relaxed : List[str] | None
        Forwarded verbatim to ``RecommendationResult.filters_relaxed``.
    llm_provider : LLMProvider | None
        If supplied, a single retry with a fix-JSON prompt is attempted before
        falling back to generic recommendations.
    messages : List[dict] | None
        The original message list sent to the LLM.  Required for the retry
        (the assistant reply + fix prompt are appended and re-sent).

    Returns
    -------
    RecommendationResult
        Always returns a result — never raises on malformed JSON.
    """
    relaxed = filters_relaxed or []
    index = _build_candidate_index(candidates)

    # ── Attempt 1: parse the initial response ─────────────────────────────────
    try:
        data = _parse_raw(raw)
        _validate_schema(data)
        recs = _map_recommendations(data, index, candidates)
        summary: Optional[str] = data.get("summary") or None
        logger.info("[parser] Parsed %d recommendations from Groq.", len(recs))
        return RecommendationResult(
            recommendations=recs,
            summary=summary,
            filters_relaxed=relaxed,
        )
    except (ValueError, KeyError) as exc:
        logger.warning("[parser] Initial parse failed: %s", exc)

    # ── Attempt 2: retry with fix-JSON prompt ─────────────────────────────────
    if llm_provider is not None and messages is not None:
        logger.info("[parser] Retrying with fix-JSON prompt …")
        retry_messages = list(messages) + [
            {"role": "assistant", "content": raw},
            {"role": "user", "content": _FIX_JSON_PROMPT},
        ]
        try:
            raw2 = llm_provider.complete(retry_messages)
            data2 = _parse_raw(raw2)
            _validate_schema(data2)
            recs2 = _map_recommendations(data2, index, candidates)
            summary2: Optional[str] = data2.get("summary") or None
            logger.info(
                "[parser] Retry succeeded — %d recommendations.", len(recs2)
            )
            return RecommendationResult(
                recommendations=recs2,
                summary=summary2,
                filters_relaxed=relaxed,
            )
        except Exception as retry_exc:
            logger.warning("[parser] Retry also failed: %s", retry_exc)

    # ── Fallback: return top-N filtered candidates with generic explanation ───
    result = _fallback_result(candidates)
    result.filters_relaxed = relaxed
    return result
