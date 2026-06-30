from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

@dataclass
class Restaurant:
    id: str
    name: str
    location: str
    cuisines: List[str]
    cost_for_two: int
    budget_tier: str  # 'Low', 'Medium', 'High'
    rating: float
    raw_metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class UserPreferences:
    location: str
    budget: str  # 'Low', 'Medium', 'High'
    cuisine: Optional[str] = None
    min_rating: Optional[float] = None
    additional_preferences: Optional[str] = None

@dataclass
class Recommendation:
    restaurant: Restaurant
    rank: int
    explanation: str

@dataclass
class RecommendationResult:
    recommendations: List[Recommendation]
    summary: Optional[str] = None
    filters_relaxed: List[str] = field(default_factory=list)
