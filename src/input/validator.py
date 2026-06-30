"""
Input validation for user restaurant-search preferences.

Validates and normalises raw user input before it reaches the structured
filter engine and Groq prompt builder.

Usage
-----
    from src.input.validator import validate_preferences

    prefs, errors = validate_preferences(
        location="koramangala",
        budget="medium",
        cuisine="North Indian",
        min_rating="4.0",
        additional_preferences="family-friendly",
    )
    if errors:
        print(errors)  # List[str] of human-readable error messages
    else:
        # prefs is a validated UserPreferences object
        ...
"""
from __future__ import annotations

import logging
from difflib import get_close_matches
from typing import Any, List, Optional, Tuple

from src.input.preferences import BudgetTier, UserPreferences

logger = logging.getLogger(__name__)

# Rating bounds
_MIN_RATING_FLOOR = 0.0
_MAX_RATING_CEILING = 5.0


def _normalise_location(raw: str, available_locations: List[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Attempts to match a raw location string to a canonical location.

    Strategy
    --------
    1. Exact match (case-insensitive).
    2. Fuzzy match using difflib with a 0.6 similarity cutoff.

    Returns
    -------
    (canonical_location, error_message)
    One of these will always be None.
    """
    if not raw or not raw.strip():
        return None, "Location is required and cannot be empty."

    raw_stripped = raw.strip()
    raw_title = raw_stripped.title()

    # 1. Exact match (case-insensitive)
    for loc in available_locations:
        if loc.lower() == raw_stripped.lower():
            return loc, None

    # 2. Fuzzy match
    close = get_close_matches(raw_title, available_locations, n=1, cutoff=0.6)
    if close:
        matched = close[0]
        logger.debug(f"Fuzzy-matched location '{raw_stripped}' -> '{matched}'")
        return matched, None

    # Failed to match
    sample = sorted(available_locations)[:5]
    return None, (
        f"Unknown location '{raw_stripped}'. "
        f"Please choose a valid neighborhood. Examples: {sample}."
    )


def validate_preferences(
    location: Any,
    budget: Any,
    cuisine: Any = None,
    min_rating: Any = None,
    additional_preferences: Any = None,
    available_locations: Optional[List[str]] = None,
) -> Tuple[Optional[UserPreferences], List[str]]:
    """
    Validates raw user inputs and returns a typed ``UserPreferences`` object.

    Parameters
    ----------
    location : str
        Required. The neighborhood / city area the user wants to dine in.
    budget : str
        Required. One of 'low', 'medium', 'high' (case-insensitive).
    cuisine : str | None
        Optional cuisine preference (e.g. 'North Indian'). Pass None for unconstrained.
    min_rating : float | str | None
        Optional minimum rating in [0.0, 5.0]. Pass None for unconstrained.
    additional_preferences : str | None
        Optional free-text soft constraints. Pass None for unconstrained.
    available_locations : List[str] | None
        Canonical location names from the catalog. Loaded lazily if not provided.

    Returns
    -------
    (UserPreferences | None, List[str])
        - If validation passes: (UserPreferences, [])
        - If validation fails: (None, [list of error messages])
    """
    errors: List[str] = []

    # --- Load available locations lazily if not supplied ---
    if available_locations is None:
        try:
            from src.data.preprocessor import get_available_locations
            available_locations = get_available_locations()
        except Exception as exc:
            logger.error(f"Could not load available locations: {exc}")
            available_locations = []

    # --- Validate location ---
    canonical_location: Optional[str] = None
    if not location or (isinstance(location, str) and not location.strip()):
        errors.append("Location is required.")
    else:
        canonical_location, loc_error = _normalise_location(str(location), available_locations)
        if loc_error:
            errors.append(loc_error)

    # --- Validate budget ---
    validated_budget: Optional[BudgetTier] = None
    if not budget or (isinstance(budget, str) and not str(budget).strip()):
        errors.append("Budget is required. Must be one of: Low, Medium, High.")
    else:
        try:
            validated_budget = BudgetTier.from_str(str(budget))
        except ValueError as exc:
            errors.append(str(exc))

    # --- Validate min_rating (optional) ---
    validated_rating: Optional[float] = None
    if min_rating is not None and str(min_rating).strip() != "":
        try:
            rating_float = float(min_rating)
            if not (_MIN_RATING_FLOOR <= rating_float <= _MAX_RATING_CEILING):
                errors.append(
                    f"min_rating must be between {_MIN_RATING_FLOOR} and "
                    f"{_MAX_RATING_CEILING}. Got {rating_float}."
                )
            else:
                validated_rating = rating_float
        except (TypeError, ValueError):
            errors.append(
                f"min_rating must be a numeric value between 0 and 5. Got '{min_rating}'."
            )

    # --- Normalise optional string fields ---
    def _clean_str(val: Any) -> Optional[str]:
        """Returns a stripped non-empty string or None."""
        if val is None:
            return None
        s = str(val).strip()
        return s if s else None

    validated_cuisine = _clean_str(cuisine)
    validated_additional = _clean_str(additional_preferences)

    # --- Return result ---
    if errors:
        return None, errors

    prefs = UserPreferences(
        location=canonical_location,  # type: ignore[arg-type]
        budget=validated_budget,       # type: ignore[arg-type]
        cuisine=validated_cuisine,
        min_rating=validated_rating,
        additional_preferences=validated_additional,
    )
    return prefs, []
