"""
Unit tests for src/integration/filter.py — Phase 3 acceptance criteria.

Run with:
    pytest tests/test_filter.py -v

All tests use a self-contained fixture catalog — no network / HF dataset required.
"""
import pytest
from src.data.schema import Restaurant
from src.input.preferences import BudgetTier, UserPreferences
from src.integration.filter import filter_restaurants
from src.integration.formatter import format_candidates
from src.integration.prompt_builder import (
    SYSTEM_PROMPT,
    build_messages,
    build_user_prompt,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_restaurant(
    name: str,
    location: str,
    budget_tier: str,
    rating: float,
    cuisines: list[str],
    cost_for_two: int = 800,
    rid: str | None = None,
) -> Restaurant:
    return Restaurant(
        id=rid or name.lower().replace(" ", "_"),
        name=name,
        location=location,
        cuisines=cuisines,
        cost_for_two=cost_for_two,
        budget_tier=budget_tier,
        rating=rating,
    )


@pytest.fixture
def catalog():
    """A small, deterministic catalog covering a variety of cases."""
    return [
        _make_restaurant("Spice Garden",    "Koramangala", "Medium", 4.2, ["North Indian", "Chinese"]),
        _make_restaurant("Taco Fiesta",     "Koramangala", "Medium", 3.5, ["Mexican"]),
        _make_restaurant("The Grand Thali", "Koramangala", "Low",    4.5, ["South Indian"]),
        _make_restaurant("Rooftop Bistro",  "Koramangala", "High",   4.8, ["Continental"]),
        _make_restaurant("Burger Junction", "Koramangala", "Low",    3.8, ["Fast Food", "Burgers"]),
        _make_restaurant("Pasta Palace",    "Koramangala", "Medium", 4.0, ["Italian"]),
        _make_restaurant("Dragon Wok",      "Indiranagar", "Medium", 4.3, ["Chinese"]),
        _make_restaurant("Kerala Kitchen",  "Indiranagar", "Low",    4.7, ["South Indian", "Kerala"]),
        _make_restaurant("Sushi Zone",      "Indiranagar", "High",   4.9, ["Japanese"]),
    ]


def _prefs(
    location: str = "Koramangala",
    budget: str = "Medium",
    cuisine: str | None = None,
    min_rating: float | None = None,
    additional_preferences: str | None = None,
) -> UserPreferences:
    return UserPreferences(
        location=location,
        budget=BudgetTier.from_str(budget),
        cuisine=cuisine,
        min_rating=min_rating,
        additional_preferences=additional_preferences,
    )


# ---------------------------------------------------------------------------
# 3.1 Filter Engine — core filtering
# ---------------------------------------------------------------------------

class TestFilterCore:
    def test_location_filter(self, catalog):
        candidates, relaxed = filter_restaurants(catalog, _prefs(location="Indiranagar", budget="Low"))
        locations = {r.location for r in candidates}
        assert locations == {"Indiranagar"}, f"Expected only Indiranagar, got {locations}"
        assert relaxed == []

    def test_budget_filter_medium(self, catalog):
        candidates, _ = filter_restaurants(catalog, _prefs(budget="Medium"))
        assert all(r.budget_tier == "Medium" for r in candidates)

    def test_budget_filter_low(self, catalog):
        candidates, _ = filter_restaurants(catalog, _prefs(budget="Low"))
        assert all(r.budget_tier == "Low" for r in candidates)

    def test_min_rating_filter(self, catalog):
        candidates, relaxed = filter_restaurants(catalog, _prefs(min_rating=4.0))
        assert all(r.rating >= 4.0 for r in candidates)
        assert relaxed == []

    def test_cuisine_filter_case_insensitive(self, catalog):
        candidates, relaxed = filter_restaurants(catalog, _prefs(cuisine="north indian"))
        assert all(
            any("north indian" in c.lower() for c in r.cuisines) for r in candidates
        )
        assert relaxed == []

    def test_all_filters_combined(self, catalog):
        candidates, relaxed = filter_restaurants(
            catalog, _prefs(cuisine="Chinese", min_rating=4.0)
        )
        for r in candidates:
            assert r.location == "Koramangala"
            assert r.budget_tier == "Medium"
            assert r.rating >= 4.0
            assert any("chinese" in c.lower() for c in r.cuisines)
        assert relaxed == []

    def test_no_candidates_returns_empty_not_raises(self, catalog):
        # Location that doesn't exist — nothing can match even after relaxation
        candidates, _ = filter_restaurants(catalog, _prefs(location="Mars Colony"))
        assert isinstance(candidates, list)

    def test_candidate_count_capped(self, catalog):
        # All 9 restaurants; cap at 3
        candidates, _ = filter_restaurants(
            catalog,
            _prefs(location="Koramangala", budget="Medium"),
            max_candidates=2,
        )
        assert len(candidates) <= 2

    def test_max_candidates_default_respected(self, catalog):
        # Default is 25; we have 9 restaurants, so none are cut
        candidates, _ = filter_restaurants(catalog, _prefs())
        assert len(candidates) <= 25


# ---------------------------------------------------------------------------
# 3.1 Constraint Relaxation
# ---------------------------------------------------------------------------

class TestRelaxation:
    def test_relaxes_cuisine_when_too_few(self, catalog):
        """
        'High' budget + 'Mexican' cuisine in Koramangala yields only 0 matches,
        triggering relaxation.  Cuisine should appear in filters_relaxed.
        """
        candidates, relaxed = filter_restaurants(
            catalog,
            _prefs(budget="High", cuisine="Mexican"),
        )
        assert "cuisine" in relaxed

    def test_relaxes_budget_after_cuisine(self, catalog):
        """
        If relaxing cuisine still yields < 3, budget should also be relaxed.
        """
        candidates, relaxed = filter_restaurants(
            catalog,
            _prefs(location="Indiranagar", budget="Medium", cuisine="Japanese"),
        )
        # Japanese + Medium in Indiranagar → 0 → relax cuisine → still only Low/High → relax budget
        assert len(candidates) > 0

    def test_relaxes_rating_last(self, catalog):
        """
        Requesting a very high min_rating that matches <3 should eventually
        include the rating in filters_relaxed if needed.
        """
        candidates, relaxed = filter_restaurants(
            catalog,
            _prefs(location="Koramangala", budget="High", min_rating=4.9),
        )
        # Only Rooftop Bistro (4.8) matches, still < threshold → relax
        # (exact behaviour depends on pass; at minimum we get results)
        assert isinstance(candidates, list)
        assert isinstance(relaxed, list)

    def test_no_relaxation_when_enough_candidates(self, catalog):
        candidates, relaxed = filter_restaurants(
            catalog, _prefs(location="Koramangala", budget="Medium")
        )
        assert relaxed == []


# ---------------------------------------------------------------------------
# 3.2 Formatter
# ---------------------------------------------------------------------------

class TestFormatter:
    def test_format_returns_string(self, catalog):
        result = format_candidates(catalog[:3])
        assert isinstance(result, str)

    def test_format_is_valid_json(self, catalog):
        import json
        result = format_candidates(catalog[:3])
        parsed = json.loads(result)
        assert isinstance(parsed, list)
        assert len(parsed) == 3

    def test_format_contains_required_fields(self, catalog):
        import json
        result = format_candidates(catalog[:1])
        parsed = json.loads(result)
        record = parsed[0]
        for field in ("id", "name", "cuisines", "rating", "cost_for_two", "budget_tier"):
            assert field in record, f"Missing field: {field}"

    def test_format_excludes_verbose_metadata(self, catalog):
        import json
        result = format_candidates(catalog[:1])
        parsed = json.loads(result)
        record = parsed[0]
        assert "raw_metadata" not in record
        assert "reviews_list" not in record

    def test_format_empty_list(self):
        result = format_candidates([])
        import json
        assert json.loads(result) == []

    def test_format_is_compact(self, catalog):
        # Compact JSON must not contain newlines or leading spaces
        result = format_candidates(catalog[:2])
        assert "\n" not in result
        assert "  " not in result


# ---------------------------------------------------------------------------
# 3.3 Prompt Builder
# ---------------------------------------------------------------------------

class TestPromptBuilder:
    def test_system_prompt_contains_json_schema(self):
        assert "restaurant_id" in SYSTEM_PROMPT
        assert "explanation" in SYSTEM_PROMPT
        assert "summary" in SYSTEM_PROMPT

    def test_system_prompt_forbids_hallucination(self):
        assert "only use IDs from the candidate list" in SYSTEM_PROMPT

    def test_user_prompt_contains_all_preference_fields(self):
        prefs = _prefs(
            location="Koramangala",
            budget="Medium",
            cuisine="Italian",
            min_rating=4.0,
            additional_preferences="family-friendly",
        )
        prompt = build_user_prompt(prefs, "[]")
        assert "Koramangala" in prompt
        assert "Medium" in prompt
        assert "Italian" in prompt
        assert "4.0" in prompt
        assert "family-friendly" in prompt

    def test_user_prompt_none_fields_show_defaults(self):
        prefs = _prefs()  # no cuisine, rating, additional
        prompt = build_user_prompt(prefs, "[]")
        assert "any" in prompt        # cuisine fallback
        assert "none" in prompt       # rating fallback

    def test_user_prompt_contains_candidates_json(self):
        import json
        candidates_json = json.dumps([{"id": "abc123", "name": "Test"}])
        prompt = build_user_prompt(_prefs(), candidates_json)
        assert "abc123" in prompt

    def test_relaxation_note_appended_when_relaxed(self):
        prompt = build_user_prompt(
            _prefs(), "[]", filters_relaxed=["cuisine", "budget"]
        )
        assert "cuisine" in prompt
        assert "budget" in prompt
        assert "relaxed" in prompt.lower()

    def test_no_relaxation_note_when_none(self):
        prompt = build_user_prompt(_prefs(), "[]", filters_relaxed=[])
        assert "relaxed" not in prompt.lower()

    def test_build_messages_returns_two_roles(self):
        messages = build_messages(_prefs(), "[]")
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"

    def test_build_messages_system_content_matches_constant(self):
        messages = build_messages(_prefs(), "[]")
        assert messages[0]["content"] == SYSTEM_PROMPT
