"""
Result renderer — Phase 5.1

Converts a ``RecommendationResult`` into display-ready Python structures
that the Streamlit UI can consume directly.  Keeping rendering logic here
(rather than inline in ``main.py``) keeps the Streamlit file thin and makes
the renderer independently testable.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from src.data.schema import RecommendationResult


@dataclass
class RenderedCard:
    """
    A single recommendation card ready for display.

    All fields are plain Python types so the renderer has no Streamlit
    dependency and can be used in unit tests.
    """
    rank: int
    name: str
    cuisines: str           # comma-joined, e.g. "North Indian, Chinese"
    rating: float
    cost_for_two: int
    budget_tier: str        # "Low" / "Medium" / "High"
    explanation: str
    online_order: str       # "Yes" / "No" / ""
    book_table: str         # "Yes" / "No" / ""
    votes: int
    rest_type: str          # e.g. "Casual Dining"
    dish_liked: str         # popular dishes string


@dataclass
class RenderedResult:
    """All the data the UI needs to render a full recommendation response."""
    cards: List[RenderedCard]
    summary: Optional[str]
    filters_relaxed: List[str]
    total_candidates_shown: int


def render_result(result: RecommendationResult) -> RenderedResult:
    """
    Convert a ``RecommendationResult`` into a ``RenderedResult``.

    Parameters
    ----------
    result : RecommendationResult
        The output of ``get_recommendations()``.

    Returns
    -------
    RenderedResult
        Flat, display-ready data structures.
    """
    cards: List[RenderedCard] = []

    for rec in result.recommendations:
        r = rec.restaurant
        meta = r.raw_metadata or {}

        card = RenderedCard(
            rank=rec.rank,
            name=r.name,
            cuisines=", ".join(r.cuisines),
            rating=r.rating,
            cost_for_two=r.cost_for_two,
            budget_tier=r.budget_tier,
            explanation=rec.explanation,
            online_order=str(meta.get("online_order", "") or ""),
            book_table=str(meta.get("book_table", "") or ""),
            votes=int(meta.get("votes", 0) or 0),
            rest_type=str(meta.get("rest_type", "") or ""),
            dish_liked=str(meta.get("dish_liked", "") or ""),
        )
        cards.append(card)

    return RenderedResult(
        cards=cards,
        summary=result.summary,
        filters_relaxed=result.filters_relaxed,
        total_candidates_shown=len(cards),
    )
