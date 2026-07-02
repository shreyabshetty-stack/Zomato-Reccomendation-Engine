"""
Mock LLM provider — Phase 4.4

Returns a deterministic JSON response for unit and integration tests
without making any network calls.

Usage
-----
>>> from src.engine.mock_provider import MockLLMProvider
>>> provider = MockLLMProvider(candidate_ids=["id1", "id2", "id3"])
>>> provider.complete([])
'{"summary": "Mock summary.", "recommendations": [{"restaurant_id": "id1", "rank": 1, ...}]}'

You can also supply a fully custom ``response`` string to test parser
behaviour with arbitrary payloads (e.g. malformed JSON, missing fields).
"""
from __future__ import annotations

import json
from typing import List, Optional


class MockLLMProvider:
    """
    A drop-in replacement for ``GroqLLMProvider`` that never touches the network.

    Parameters
    ----------
    candidate_ids : List[str] | None
        Restaurant IDs to embed in the mock ``recommendations`` list.
        The first ``top_n`` IDs are used; ranks are assigned in order.
        When ``None``, an empty recommendations list is returned unless
        ``response`` is also provided.
    top_n : int
        How many recommendations to include in the mock response.
    summary : str | None
        Optional summary text to include.  Defaults to ``"Mock summary."``.
    response : str | None
        If supplied, this raw string is returned verbatim, ignoring all other
        parameters.  Useful for testing malformed-JSON paths.
    """

    def __init__(
        self,
        candidate_ids: Optional[List[str]] = None,
        top_n: int = 5,
        summary: Optional[str] = "Mock summary.",
        response: Optional[str] = None,
    ) -> None:
        self._candidate_ids = candidate_ids or []
        self._top_n = top_n
        self._summary = summary
        self._custom_response = response

    # ── LLMProvider interface ─────────────────────────────────────────────────

    def complete(self, messages: List[dict]) -> str:  # noqa: ARG002
        """
        Return the mock response.

        ``messages`` is accepted to satisfy the ``LLMProvider`` protocol but
        is intentionally ignored.
        """
        if self._custom_response is not None:
            return self._custom_response

        ids = self._candidate_ids[: self._top_n]
        recommendations = [
            {
                "restaurant_id": rid,
                "rank": rank,
                "explanation": (
                    f"Mock explanation for restaurant {rid} (rank {rank})."
                ),
            }
            for rank, rid in enumerate(ids, start=1)
        ]
        payload = {
            "summary": self._summary,
            "recommendations": recommendations,
        }
        return json.dumps(payload)
