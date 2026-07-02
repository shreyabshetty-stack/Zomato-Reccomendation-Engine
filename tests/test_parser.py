"""
Unit tests for src/engine/parser.py (Phase 4 & 6).

Run with:
    pytest tests/test_parser.py -v
"""
import pytest
from src.data.schema import Restaurant, RecommendationResult
from src.engine.parser import parse_groq_response


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def candidates():
    return [
        Restaurant(
            id="rest1",
            name="The Gourmet Sourdough",
            location="Indiranagar",
            cuisines=["Italian", "Pizza"],
            cost_for_two=1800,
            budget_tier="High",
            rating=4.9,
        ),
        Restaurant(
            id="rest2",
            name="Nonna's Kitchen",
            location="Indiranagar",
            cuisines=["Italian"],
            cost_for_two=1200,
            budget_tier="Medium",
            rating=4.7,
        ),
        Restaurant(
            id="rest3",
            name="Oven & Oak",
            location="Indiranagar",
            cuisines=["Pizza", "Italian"],
            cost_for_two=1500,
            budget_tier="Medium",
            rating=4.5,
        ),
    ]


class DummyLLMProvider:
    def __init__(self, response_str: str):
        self.response_str = response_str
        self.calls = []

    def complete(self, messages: list[dict]) -> str:
        self.calls.append(messages)
        return self.response_str


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_parse_valid_response(candidates):
    raw = """{
        "summary": "Highly recommended Italian spots near Indiranagar.",
        "recommendations": [
            {"restaurant_id": "rest2", "rank": 1, "explanation": "Authentic pasta."},
            {"restaurant_id": "rest1", "rank": 2, "explanation": "Perfect wood-fired sourdough crust."}
        ]
    }"""

    result = parse_groq_response(raw, candidates, filters_relaxed=["min_rating"])

    assert isinstance(result, RecommendationResult)
    assert result.summary == "Highly recommended Italian spots near Indiranagar."
    assert result.filters_relaxed == ["min_rating"]
    assert len(result.recommendations) == 2

    # Verify ranking sorting and mapping
    rec1 = result.recommendations[0]
    assert rec1.rank == 1
    assert rec1.restaurant.id == "rest2"
    assert rec1.restaurant.name == "Nonna's Kitchen"
    assert rec1.explanation == "Authentic pasta."

    rec2 = result.recommendations[1]
    assert rec2.rank == 2
    assert rec2.restaurant.id == "rest1"
    assert rec2.restaurant.name == "The Gourmet Sourdough"
    assert rec2.explanation == "Perfect wood-fired sourdough crust."


def test_parse_missing_summary_or_none(candidates):
    raw = """{
        "recommendations": [
            {"restaurant_id": "rest3", "rank": 1, "explanation": "Great vibe."}
        ]
    }"""
    result = parse_groq_response(raw, candidates)
    assert isinstance(result, RecommendationResult)
    assert result.summary is None
    assert len(result.recommendations) == 1
    assert result.recommendations[0].restaurant.id == "rest3"


def test_parse_unknown_id_skips_item(candidates):
    raw = """{
        "summary": "Skipping unknown entries",
        "recommendations": [
            {"restaurant_id": "unknown_id_here", "rank": 1, "explanation": "Should be skipped."},
            {"restaurant_id": "rest2", "rank": 2, "explanation": "Should be included."}
        ]
    }"""
    result = parse_groq_response(raw, candidates)
    assert len(result.recommendations) == 1
    assert result.recommendations[0].restaurant.id == "rest2"
    assert result.recommendations[0].rank == 2


def test_parse_malformed_json_no_provider_fallback(candidates):
    # Syntax error in JSON
    raw = "{ malformed json: true "
    result = parse_groq_response(raw, candidates, filters_relaxed=["budget"])

    assert isinstance(result, RecommendationResult)
    assert result.filters_relaxed == ["budget"]
    # Check that fallback strategy works (grabs top candidates)
    assert len(result.recommendations) > 0
    assert result.recommendations[0].restaurant.id == "rest1"  # First candidate
    assert "AI ranking was unavailable" in result.summary


def test_parse_invalid_schema_no_provider_fallback(candidates):
    # Valid JSON but completely missing 'recommendations' key
    raw = '{"wrong_key": []}'
    result = parse_groq_response(raw, candidates)
    assert len(result.recommendations) > 0
    assert result.recommendations[0].restaurant.id == "rest1"
    assert "AI ranking was unavailable" in result.summary


def test_parse_retry_success(candidates):
    malformed_raw = "{ malformed json "
    valid_corrected = """{
        "summary": "Recovered summary",
        "recommendations": [
            {"restaurant_id": "rest3", "rank": 1, "explanation": "Recovered description."}
        ]
    }"""
    provider = DummyLLMProvider(valid_corrected)
    messages = [{"role": "user", "content": "original query"}]

    result = parse_groq_response(
        malformed_raw,
        candidates,
        llm_provider=provider,
        messages=messages,
    )

    assert isinstance(result, RecommendationResult)
    assert result.summary == "Recovered summary"
    assert len(result.recommendations) == 1
    assert result.recommendations[0].restaurant.id == "rest3"
    assert result.recommendations[0].explanation == "Recovered description."
    # Ensure complete was called on the mock provider
    assert len(provider.calls) == 1
    # Check that fix prompt message was appended
    assert provider.calls[0][-1]["role"] == "user"
    assert "Your previous response was not valid JSON" in provider.calls[0][-1]["content"]


def test_parse_retry_failure_fallback(candidates):
    malformed_raw = "{ malformed "
    still_malformed = "{ still bad "
    provider = DummyLLMProvider(still_malformed)
    messages = [{"role": "user", "content": "original query"}]

    result = parse_groq_response(
        malformed_raw,
        candidates,
        llm_provider=provider,
        messages=messages,
    )

    assert isinstance(result, RecommendationResult)
    assert "AI ranking was unavailable" in result.summary
    assert len(result.recommendations) == len(candidates)
    assert result.recommendations[0].restaurant.id == "rest1"
