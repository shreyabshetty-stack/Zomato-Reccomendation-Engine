"""
Candidate formatter — Phase 3.2

Converts a list of ``Restaurant`` objects into compact JSON suitable for
inclusion in an LLM prompt.  Only the fields the model actually needs
are serialised; verbose ones like ``reviews_list`` or ``raw_metadata``
are intentionally excluded to keep token counts low.
"""
from __future__ import annotations

import json
from typing import List

from src.data.schema import Restaurant


def format_candidates(restaurants: List[Restaurant]) -> str:
    """
    Serialise a list of ``Restaurant`` objects to a compact JSON string.

    Included fields
    ---------------
    id, name, cuisines, rating, cost_for_two, budget_tier

    Returns
    -------
    str
        A single-line JSON array (no indentation) ready for prompt injection.
    """
    payload = [
        {
            "id": r.id,
            "name": r.name,
            "cuisines": r.cuisines,
            "rating": r.rating,
            "cost_for_two": r.cost_for_two,
            "budget_tier": r.budget_tier,
        }
        for r in restaurants
    ]
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
