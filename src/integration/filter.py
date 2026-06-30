"""
Structured filter engine — Phase 3.1

Filters the in-memory restaurant catalog against hard constraints derived
from a validated ``UserPreferences`` object, then returns at most
``MAX_CANDIDATES`` results.

Constraint relaxation
---------------------
Relaxation is only triggered when the current pass produces **zero** results.
The relaxation order is:
  1. cuisine  (if specified)
  2. budget tier
  3. minimum rating

All relaxed field names are recorded and returned so the caller (and
eventually the UI) can inform the user about the trade-off.
"""
from __future__ import annotations

import logging
from typing import List, Tuple

from src import config
from src.data.schema import Restaurant
from src.input.preferences import UserPreferences

logger = logging.getLogger(__name__)


def _filter_strict(
    catalog: List[Restaurant],
    prefs: UserPreferences,
    *,
    use_cuisine: bool = True,
    use_budget: bool = True,
    use_rating: bool = True,
) -> List[Restaurant]:
    """
    Applies a subset of hard filters to the catalog, controlled by flags
    so the relaxation loop can toggle them individually.
    """
    results = []
    for r in catalog:
        # ── Location (always required) ──────────────────────────────────────
        if r.location.lower() != prefs.location.lower():
            continue

        # ── Budget tier ─────────────────────────────────────────────────────
        if use_budget and r.budget_tier.lower() != prefs.budget.value.lower():
            continue

        # ── Minimum rating ──────────────────────────────────────────────────
        if use_rating and prefs.min_rating is not None:
            if r.rating < prefs.min_rating:
                continue

        # ── Cuisine (substring, case-insensitive) ────────────────────────────
        if use_cuisine and prefs.cuisine:
            cuisine_pref = prefs.cuisine.lower()
            if not any(cuisine_pref in c.lower() for c in r.cuisines):
                continue

        results.append(r)
    return results


def filter_restaurants(
    catalog: List[Restaurant],
    prefs: UserPreferences,
    max_candidates: int | None = None,
) -> Tuple[List[Restaurant], List[str]]:
    """
    Filter ``catalog`` by ``prefs`` and return the top ``max_candidates``.

    Relaxation is only attempted when a pass produces **zero** results.

    Parameters
    ----------
    catalog : List[Restaurant]
        Full preprocessed restaurant list from the Data Layer.
    prefs : UserPreferences
        Validated user preferences (Phase 2 output).
    max_candidates : int | None
        Override the global ``MAX_CANDIDATES`` setting. Defaults to
        ``config.MAX_CANDIDATES`` (25).

    Returns
    -------
    (candidates, filters_relaxed)
        candidates      – List of ``Restaurant`` objects (length ≤ max_candidates)
        filters_relaxed – List of field names that were relaxed (may be empty)
    """
    cap = max_candidates if max_candidates is not None else config.MAX_CANDIDATES
    filters_relaxed: List[str] = []

    # ── Pass 1: all filters ──────────────────────────────────────────────────
    candidates = _filter_strict(catalog, prefs)
    logger.debug(f"[filter] Pass 1 (all filters): {len(candidates)} candidates")

    if candidates:
        return candidates[:cap], filters_relaxed

    # ── Pass 2: relax cuisine (only if cuisine was specified) ────────────────
    if prefs.cuisine:
        candidates = _filter_strict(catalog, prefs, use_cuisine=False)
        logger.debug(f"[filter] Pass 2 (no cuisine): {len(candidates)} candidates")
        if candidates:
            filters_relaxed.append("cuisine")
            return candidates[:cap], filters_relaxed

    # ── Pass 3: relax budget ─────────────────────────────────────────────────
    candidates = _filter_strict(
        catalog, prefs, use_cuisine=False, use_budget=False
    )
    logger.debug(f"[filter] Pass 3 (no cuisine, no budget): {len(candidates)} candidates")
    if candidates:
        if prefs.cuisine:
            filters_relaxed.append("cuisine")
        filters_relaxed.append("budget")
        return candidates[:cap], filters_relaxed

    # ── Pass 4: relax rating ─────────────────────────────────────────────────
    candidates = _filter_strict(
        catalog, prefs, use_cuisine=False, use_budget=False, use_rating=False
    )
    logger.debug(f"[filter] Pass 4 (no cuisine, no budget, no rating): {len(candidates)} candidates")
    if candidates:
        if prefs.cuisine:
            filters_relaxed.append("cuisine")
        filters_relaxed.append("budget")
        if prefs.min_rating is not None:
            filters_relaxed.append("min_rating")

    return candidates[:cap], filters_relaxed
