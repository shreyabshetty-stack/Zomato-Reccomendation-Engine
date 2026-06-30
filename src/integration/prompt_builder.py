"""
Prompt builder — Phase 3.3

Builds the system prompt and user prompt that are sent to Groq.
Templates follow architecture.md §6.1 and §6.2.
"""
from __future__ import annotations

from typing import List, Optional

from src.input.preferences import UserPreferences

# ── System prompt ────────────────────────────────────────────────────────────
# Instructs the LLM about its role and enforces structured JSON output.
SYSTEM_PROMPT = """\
You are a restaurant recommendation assistant for an app similar to Zomato.
You receive a user's dining preferences and a list of candidate restaurants
(already filtered by location, budget, and rating).

Your tasks:
1. Rank the top 5 restaurants that best match the user's preferences.
2. For each, write a concise explanation (1-2 sentences) of why it fits.
3. Optionally provide a one-sentence summary of the overall selection.

Consider soft preferences (cuisine taste, family-friendly, quick service)
when ranking. Do not invent restaurants—only use IDs from the candidate list.

Respond ONLY with valid JSON in this schema:
{
  "summary": "string or null",
  "recommendations": [
    {
      "restaurant_id": "string",
      "rank": 1,
      "explanation": "string"
    }
  ]
}"""


def build_user_prompt(
    prefs: UserPreferences,
    candidates_json: str,
    filters_relaxed: Optional[List[str]] = None,
) -> str:
    """
    Builds the user-turn prompt to send to Groq alongside the system prompt.

    Parameters
    ----------
    prefs : UserPreferences
        Validated, normalised user preferences (Phase 2 output).
    candidates_json : str
        Compact JSON array of candidate restaurants (Phase 3.2 output).
    filters_relaxed : List[str] | None
        Names of any filters that were relaxed to produce this candidate list.
        If non-empty, a note is appended to the prompt so the LLM can
        acknowledge the trade-off in its explanation.

    Returns
    -------
    str
        The fully assembled user-turn message for the Groq API call.
    """
    cuisine_str = prefs.cuisine or "any"
    rating_str = str(prefs.min_rating) if prefs.min_rating is not None else "none"
    additional_str = prefs.additional_preferences or "none"

    lines = [
        "User preferences:",
        f"- Location: {prefs.location}",
        f"- Budget: {prefs.budget.value}",
        f"- Cuisine: {cuisine_str}",
        f"- Minimum rating: {rating_str}",
        f"- Additional preferences: {additional_str}",
        "",
        "Candidate restaurants:",
        candidates_json,
    ]

    # Append relaxation notice if applicable
    if filters_relaxed:
        relaxed_readable = ", ".join(filters_relaxed)
        lines += [
            "",
            f"Note: The following filters were relaxed to find enough candidates: "
            f"{relaxed_readable}. Please acknowledge this briefly in your explanations.",
        ]

    return "\n".join(lines)


def build_messages(
    prefs: UserPreferences,
    candidates_json: str,
    filters_relaxed: Optional[List[str]] = None,
) -> List[dict]:
    """
    Returns the ``messages`` list expected by the Groq chat completion API.

    Parameters
    ----------
    prefs : UserPreferences
    candidates_json : str
    filters_relaxed : List[str] | None

    Returns
    -------
    List[dict]
        [{"role": "system", "content": ...}, {"role": "user", "content": ...}]
    """
    user_prompt = build_user_prompt(prefs, candidates_json, filters_relaxed)
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
