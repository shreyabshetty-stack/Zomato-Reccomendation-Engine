"""
User preference model for restaurant filtering.

This module defines the `BudgetTier` enum and `UserPreferences` dataclass
used across the pipeline (validator -> filter engine -> prompt builder).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class BudgetTier(str, Enum):
    """Budget tiers aligned with the preprocessor's cost-based classification."""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"

    @classmethod
    def from_str(cls, value: str) -> "BudgetTier":
        """
        Case-insensitive lookup from a raw string.
        Raises ValueError with a clear message on failure.
        """
        normalized = value.strip().title()
        for member in cls:
            if member.value == normalized:
                return member
        valid = [m.value for m in cls]
        raise ValueError(
            f"Invalid budget tier '{value}'. Must be one of: {valid}."
        )


@dataclass
class UserPreferences:
    """
    Holds validated user preferences used to filter and rank restaurants.

    Fields
    ------
    location : str
        Required. The neighborhood / city area the user wants to dine in.
        Stored in canonical title-case after validation (e.g., 'Koramangala').
    budget : BudgetTier
        Required. Budget tier: Low (<=500 Rs), Medium (501-1500 Rs), High (>1500 Rs).
    cuisine : Optional[str]
        Preferred cuisine type (e.g., 'North Indian'). ``None`` = unconstrained.
    min_rating : Optional[float]
        Minimum acceptable star rating in [0.0, 5.0]. ``None`` = unconstrained.
    additional_preferences : Optional[str]
        Free-text soft constraints (e.g., 'family-friendly, outdoor seating').
        Passed verbatim to the LLM prompt. ``None`` = unconstrained.
    """
    location: str
    budget: BudgetTier
    cuisine: Optional[str] = None
    min_rating: Optional[float] = None
    additional_preferences: Optional[str] = None

    def budget_label(self) -> str:
        """Returns the string label of the budget tier (e.g. 'Low')."""
        return self.budget.value
