"""
Unit tests for src/input/validator.py (Phase 2 acceptance criteria).

Run with:
    pytest tests/test_validator.py -v
"""
import pytest
from src.input.preferences import BudgetTier, UserPreferences
from src.input.validator import validate_preferences

# A fixed small list of canonical locations for deterministic tests
# (avoids any dependency on the network / HF dataset being downloaded)
LOCATIONS = [
    "Banashankari",
    "Banaswadi",
    "Basavanagudi",
    "Indiranagar",
    "Koramangala",
    "Jayanagar",
    "Whitefield",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _validate(**kwargs):
    """Shorthand that injects the LOCATIONS fixture."""
    return validate_preferences(available_locations=LOCATIONS, **kwargs)


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------

class TestValidHappyPath:
    def test_all_fields_provided(self):
        prefs, errors = _validate(
            location="Koramangala",
            budget="Medium",
            cuisine="North Indian",
            min_rating="4.0",
            additional_preferences="family-friendly",
        )
        assert errors == []
        assert isinstance(prefs, UserPreferences)
        assert prefs.location == "Koramangala"
        assert prefs.budget == BudgetTier.MEDIUM
        assert prefs.cuisine == "North Indian"
        assert prefs.min_rating == pytest.approx(4.0)
        assert prefs.additional_preferences == "family-friendly"

    def test_only_required_fields(self):
        prefs, errors = _validate(location="Indiranagar", budget="Low")
        assert errors == []
        assert prefs.cuisine is None
        assert prefs.min_rating is None
        assert prefs.additional_preferences is None

    def test_budget_case_insensitive_lower(self):
        prefs, errors = _validate(location="Whitefield", budget="low")
        assert errors == []
        assert prefs.budget == BudgetTier.LOW

    def test_budget_case_insensitive_upper(self):
        prefs, errors = _validate(location="Whitefield", budget="HIGH")
        assert errors == []
        assert prefs.budget == BudgetTier.HIGH

    def test_budget_case_insensitive_mixed(self):
        prefs, errors = _validate(location="Whitefield", budget="mEdIuM")
        assert errors == []
        assert prefs.budget == BudgetTier.MEDIUM

    def test_location_case_insensitive_exact(self):
        prefs, errors = _validate(location="koramangala", budget="Low")
        assert errors == []
        assert prefs.location == "Koramangala"

    def test_location_fuzzy_match(self):
        # Slightly misspelled – should still resolve via fuzzy matching
        prefs, errors = _validate(location="Koramagala", budget="Low")
        assert errors == []
        assert prefs.location == "Koramangala"

    def test_min_rating_boundary_zero(self):
        prefs, errors = _validate(location="Whitefield", budget="Medium", min_rating="0.0")
        assert errors == []
        assert prefs.min_rating == pytest.approx(0.0)

    def test_min_rating_boundary_five(self):
        prefs, errors = _validate(location="Whitefield", budget="Medium", min_rating="5.0")
        assert errors == []
        assert prefs.min_rating == pytest.approx(5.0)

    def test_empty_optional_strings_become_none(self):
        prefs, errors = _validate(
            location="Indiranagar",
            budget="Medium",
            cuisine="",
            min_rating=None,
            additional_preferences="   ",
        )
        assert errors == []
        assert prefs.cuisine is None
        assert prefs.additional_preferences is None


# ---------------------------------------------------------------------------
# Invalid budget
# ---------------------------------------------------------------------------

class TestInvalidBudget:
    def test_missing_budget(self):
        _, errors = _validate(location="Indiranagar", budget="")
        assert any("budget" in e.lower() for e in errors)

    def test_budget_none(self):
        _, errors = _validate(location="Indiranagar", budget=None)
        assert any("budget" in e.lower() for e in errors)

    def test_budget_typo(self):
        _, errors = _validate(location="Indiranagar", budget="expenseve")
        assert len(errors) >= 1

    def test_budget_numeric(self):
        _, errors = _validate(location="Indiranagar", budget=500)
        assert len(errors) >= 1


# ---------------------------------------------------------------------------
# Invalid rating
# ---------------------------------------------------------------------------

class TestInvalidRating:
    def test_rating_above_five(self):
        _, errors = _validate(location="Whitefield", budget="Medium", min_rating="5.1")
        assert any("min_rating" in e.lower() or "rating" in e.lower() for e in errors)

    def test_rating_negative(self):
        _, errors = _validate(location="Whitefield", budget="Medium", min_rating="-1")
        assert len(errors) >= 1

    def test_rating_non_numeric(self):
        _, errors = _validate(location="Whitefield", budget="Medium", min_rating="great")
        assert len(errors) >= 1


# ---------------------------------------------------------------------------
# Invalid / unknown location
# ---------------------------------------------------------------------------

class TestInvalidLocation:
    def test_missing_location(self):
        _, errors = _validate(location="", budget="Low")
        assert any("location" in e.lower() for e in errors)

    def test_location_none(self):
        _, errors = _validate(location=None, budget="Low")
        assert any("location" in e.lower() for e in errors)

    def test_unknown_location(self):
        _, errors = _validate(location="Mars Colony 7", budget="Low")
        assert any("location" in e.lower() or "unknown" in e.lower() for e in errors)


# ---------------------------------------------------------------------------
# Multiple simultaneous errors are collected
# ---------------------------------------------------------------------------

class TestMultipleErrors:
    def test_both_location_and_budget_invalid(self):
        _, errors = _validate(location="", budget="")
        assert len(errors) >= 2

    def test_all_fields_invalid(self):
        _, errors = _validate(
            location="",
            budget="foo",
            min_rating="99",
        )
        assert len(errors) >= 3


# ---------------------------------------------------------------------------
# BudgetTier enum helper
# ---------------------------------------------------------------------------

class TestBudgetTierEnum:
    def test_from_str_valid_values(self):
        assert BudgetTier.from_str("low") == BudgetTier.LOW
        assert BudgetTier.from_str("Medium") == BudgetTier.MEDIUM
        assert BudgetTier.from_str("HIGH") == BudgetTier.HIGH

    def test_from_str_invalid_raises(self):
        with pytest.raises(ValueError, match="Invalid budget tier"):
            BudgetTier.from_str("luxury")
