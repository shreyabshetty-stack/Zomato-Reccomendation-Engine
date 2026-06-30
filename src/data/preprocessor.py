import hashlib
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from src import config
from src.data.schema import Restaurant
from src.data.loader import load_raw_dataset
from src.data.cache import save_to_cache, load_from_cache

logger = logging.getLogger(__name__)

# Global in-memory catalog
_catalog: List[Restaurant] = []
_locations: List[str] = []

def parse_rating(rate_str: Any) -> Optional[float]:
    """
    Coerces raw rating string (e.g., '4.1/5', 'NEW', '-') to a float.
    Returns None if the rating is completely invalid or cannot be parsed.
    """
    if not rate_str or not isinstance(rate_str, str):
        return None
    rate_str = rate_str.strip()
    if rate_str in ("NEW", "-", ""):
        return 0.0  # Treat new or unrated restaurants as 0.0 instead of skipping
    if "/" in rate_str:
        rate_str = rate_str.split("/")[0].strip()
    try:
        return float(rate_str)
    except ValueError:
        return None

def parse_cost(cost_str: Any) -> Optional[int]:
    """
    Parses approximate cost for two people from raw string (e.g., '800', '1,200') to integer.
    """
    if cost_str is None:
        return None
    if isinstance(cost_str, (int, float)):
        return int(cost_str)
    if not isinstance(cost_str, str):
        return None
    cost_str = cost_str.strip().replace(",", "")
    try:
        return int(cost_str)
    except ValueError:
        return None

def map_budget_tier(cost_for_two: int) -> str:
    """
    Assigns a budget tier based on cost for two:
    - Low: <= 500
    - Medium: 501 - 1500
    - High: > 1500
    """
    if cost_for_two <= 500:
        return "Low"
    elif cost_for_two <= 1500:
        return "Medium"
    else:
        return "High"

def generate_id(name: str, address: str) -> str:
    """
    Generates a deterministic unique ID for a restaurant based on its name and address.
    """
    key = f"{name.lower().strip()}|{address.lower().strip()}"
    return hashlib.md5(key.encode("utf-8")).hexdigest()

def normalize_location(loc_str: Any) -> str:
    """
    Cleans and title-cases location strings.
    """
    if not loc_str or not isinstance(loc_str, str):
        return "Unknown"
    loc_str = loc_str.strip().title()
    # Normalize common alias variations if any (e.g. Bengaluru -> Bangalore)
    if loc_str in ("Bengaluru", "Bangalore"):
        loc_str = "Bangalore"
    return loc_str

def preprocess_records(raw_records: List[Dict[str, Any]]) -> List[Restaurant]:
    """
    Processes raw records into clean, validated, and deduplicated Restaurant objects.
    """
    logger.info("Starting preprocessing of raw records...")
    processed_restaurants: List[Restaurant] = []
    seen_ids: Set[str] = set()
    
    for i, record in enumerate(raw_records):
        name = record.get("name")
        address = record.get("address")
        
        # Validation: Name is required
        if not name or not isinstance(name, str):
            continue
            
        # Fallback address if empty
        address_str = address.strip() if (address and isinstance(address, str)) else "No Address Provided"
        
        # 1. Generate unique ID
        res_id = generate_id(name, address_str)
        
        # Deduplication check
        if res_id in seen_ids:
            continue
            
        # 2. Parse cost
        raw_cost = record.get("approx_cost(for two people)")
        cost = parse_cost(raw_cost)
        if cost is None or cost <= 0:
            # Skip records without a valid price since filtering relies heavily on budget
            continue
            
        # 3. Parse rating
        raw_rate = record.get("rate")
        rating = parse_rating(raw_rate)
        if rating is None:
            # Skip invalid ratings
            continue
            
        # 4. Normalize location
        raw_loc = record.get("location")
        location = normalize_location(raw_loc)
        
        # 5. Parse cuisines
        raw_cuisines = record.get("cuisines", "")
        cuisines_list: List[str] = []
        if isinstance(raw_cuisines, str) and raw_cuisines.strip():
            cuisines_list = [c.strip().title() for c in raw_cuisines.split(",") if c.strip()]
        
        if not cuisines_list:
            # Fallback if cuisines are empty
            cuisines_list = ["Other"]
            
        # 6. Assign budget tier
        budget_tier = map_budget_tier(cost)
        
        # 7. Collect raw metadata (phone, book_table, online_order, votes, listed_in)
        metadata = {
            "url": record.get("url", ""),
            "phone": record.get("phone", ""),
            "online_order": record.get("online_order", ""),
            "book_table": record.get("book_table", ""),
            "votes": record.get("votes", 0),
            "rest_type": record.get("rest_type", ""),
            "dish_liked": record.get("dish_liked", ""),
            "listed_in_type": record.get("listed_in(type)", ""),
            "listed_in_city": record.get("listed_in(city)", ""),
            "address": address_str
        }
        
        restaurant = Restaurant(
            id=res_id,
            name=name.strip(),
            location=location,
            cuisines=cuisines_list,
            cost_for_two=cost,
            budget_tier=budget_tier,
            rating=rating,
            raw_metadata=metadata
        )
        
        processed_restaurants.append(restaurant)
        seen_ids.add(res_id)
        
    logger.info(f"Preprocessing completed. Kept {len(processed_restaurants)} unique valid restaurants out of {len(raw_records)} raw records.")
    return processed_restaurants

def get_catalog(force_reload: bool = False) -> List[Restaurant]:
    """
    Retrieves the restaurant catalog. Uses memory cache first, then disk cache,
    and falls back to loading and preprocessing from the Hugging Face dataset.
    """
    global _catalog, _locations
    
    if _catalog and not force_reload:
        return _catalog
        
    # Get cache path from config
    cache_path = config.DATASET_CACHE_PATH
    if cache_path is None:
        # Default cache location in the workspace root
        cache_path = Path(__file__).resolve().parent.parent.parent / ".cache" / "preprocessed_catalog.pkl"
        
    # Try loading from cache if not forcing reload
    if not force_reload:
        cached_data = load_from_cache(cache_path)
        if cached_data is not None:
            _catalog = cached_data
            _locations = sorted(list(set(r.location for r in _catalog)))
            return _catalog
            
    # Fallback: Load raw and preprocess
    try:
        raw_records = load_raw_dataset()
        _catalog = preprocess_records(raw_records)
        
        # Save to cache
        save_to_cache(_catalog, cache_path)
        
        # Populate location listing
        _locations = sorted(list(set(r.location for r in _catalog)))
    except Exception as e:
        logger.exception("Failed to build the restaurant catalog")
        raise e
        
    return _catalog

def get_available_locations() -> List[str]:
    """
    Returns the list of unique title-cased locations/neighborhoods available in the dataset.
    """
    global _locations
    if not _locations:
        # Initialize catalog if not already loaded
        get_catalog()
    return _locations
