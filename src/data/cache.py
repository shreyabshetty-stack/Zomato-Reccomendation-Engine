import logging
import pickle
from pathlib import Path
from typing import Any, List, Optional
from src.data.schema import Restaurant

logger = logging.getLogger(__name__)

def save_to_cache(restaurants: List[Restaurant], cache_path: Path) -> bool:
    """
    Serializes the preprocessed catalog of Restaurant objects to a file using pickle.
    """
    try:
        # Create parent directories if they don't exist
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(cache_path, "wb") as f:
            pickle.dump(restaurants, f)
            
        logger.info(f"Successfully cached {len(restaurants)} restaurants to {cache_path}")
        return True
    except Exception as e:
        logger.warning(f"Failed to save catalog to cache at {cache_path}: {e}")
        return False

def load_from_cache(cache_path: Path) -> Optional[List[Restaurant]]:
    """
    Loads the serialized catalog of Restaurant objects from the cache file.
    Returns None if cache does not exist or fails to load.
    """
    if not cache_path.exists():
        logger.debug(f"Cache file {cache_path} does not exist.")
        return None
        
    try:
        with open(cache_path, "rb") as f:
            restaurants = pickle.load(f)
            
        if isinstance(restaurants, list) and all(isinstance(r, Restaurant) for r in restaurants):
            logger.info(f"Successfully loaded {len(restaurants)} restaurants from cache: {cache_path}")
            return restaurants
        else:
            logger.warning("Cache file did not contain a valid list of Restaurant objects.")
            return None
    except Exception as e:
        logger.warning(f"Failed to load catalog from cache at {cache_path}: {e}")
        return None
