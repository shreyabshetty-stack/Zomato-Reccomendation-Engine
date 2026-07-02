"""
Quick end-to-end smoke test for Phase 4 using MockLLMProvider.
Run from the project root: .venv\Scripts\python.exe smoke_test_phase4.py
"""
import sys

# Force UTF-8 output (for Windows terminals with cp1252)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.data.schema import Restaurant
from src.engine.mock_provider import MockLLMProvider
from src.engine.recommender import get_recommendations
from src.input.preferences import BudgetTier, UserPreferences

# Build a minimal fake catalog
catalog = [
    Restaurant(
        id="r1",
        name="Trattoria Bella",
        location="Koramangala",
        cuisines=["Italian"],
        cost_for_two=1200,
        budget_tier="Medium",
        rating=4.5,
    ),
    Restaurant(
        id="r2",
        name="Curry Palace",
        location="Koramangala",
        cuisines=["North Indian"],
        cost_for_two=900,
        budget_tier="Medium",
        rating=4.2,
    ),
    Restaurant(
        id="r3",
        name="Noodle House",
        location="Koramangala",
        cuisines=["Chinese"],
        cost_for_two=800,
        budget_tier="Medium",
        rating=4.0,
    ),
]

# ── Test 1: With cuisine filter (only r1 passes) ──────────────────────────────
print("=" * 60)
print("Test 1: Cuisine filter (Italian) — only r1 passes filter")
print("=" * 60)
prefs1 = UserPreferences(
    location="Koramangala",
    budget=BudgetTier.MEDIUM,
    cuisine="Italian",
    min_rating=4.0,
    additional_preferences="romantic dinner",
)
mock1 = MockLLMProvider(candidate_ids=["r1"], top_n=3)
result1 = get_recommendations(prefs1, catalog, llm_provider=mock1)
print(f"Summary: {result1.summary}")
print(f"Filters relaxed: {result1.filters_relaxed or 'none'}")
for rec in result1.recommendations:
    print(
        f"  [{rec.rank}] {rec.restaurant.name} "
        f"({', '.join(rec.restaurant.cuisines)}) "
        f"| Rating: {rec.restaurant.rating} "
        f"| Rs.{rec.restaurant.cost_for_two} for two"
    )
    print(f"       {rec.explanation}")
print()

# ── Test 2: No cuisine filter (all 3 pass) ────────────────────────────────────
print("=" * 60)
print("Test 2: No cuisine filter — all 3 candidates pass")
print("=" * 60)
prefs2 = UserPreferences(
    location="Koramangala",
    budget=BudgetTier.MEDIUM,
    min_rating=4.0,
)
mock2 = MockLLMProvider(candidate_ids=["r1", "r2", "r3"], top_n=3)
result2 = get_recommendations(prefs2, catalog, llm_provider=mock2)
print(f"Summary: {result2.summary}")
print(f"Filters relaxed: {result2.filters_relaxed or 'none'}")
for rec in result2.recommendations:
    print(
        f"  [{rec.rank}] {rec.restaurant.name} "
        f"({', '.join(rec.restaurant.cuisines)}) "
        f"| Rating: {rec.restaurant.rating} "
        f"| Rs.{rec.restaurant.cost_for_two} for two"
    )
    print(f"       {rec.explanation}")
print()

# ── Test 3: Malformed JSON fallback ───────────────────────────────────────────
print("=" * 60)
print("Test 3: Malformed JSON -> fallback to top-N candidates")
print("=" * 60)
mock3 = MockLLMProvider(response="THIS IS NOT JSON {{{}}")
result3 = get_recommendations(prefs2, catalog, llm_provider=mock3)
print(f"Summary: {result3.summary}")
print(f"Recs count: {len(result3.recommendations)}")
for rec in result3.recommendations:
    print(f"  [{rec.rank}] {rec.restaurant.name}")
print()

print("=" * 60)
print("Phase 4 Smoke Test PASSED")
print("=" * 60)
