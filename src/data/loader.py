import logging
from typing import Any, Dict, List
import datasets

logger = logging.getLogger(__name__)

def load_raw_dataset() -> List[Dict[str, Any]]:
    """
    Loads the raw Zomato restaurant recommendation dataset from Hugging Face.
    
    Dataset name: ManikaSaini/zomato-restaurant-recommendation
    
    Raw Columns Mapping context:
    - name: Restaurant name
    - location: Area location
    - cuisines: Comma separated cuisine strings
    - approx_cost(for two people): Estimated cost for two (string, may contain commas)
    - rate: Rating (string, e.g., '4.1/5', 'NEW', '-')
    - votes: Number of votes (int)
    - address: Complete address string
    - online_order: 'Yes'/'No'
    - book_table: 'Yes'/'No'
    - rest_type: Type of restaurant
    - dish_liked: Popular dishes
    - reviews_list: List of raw reviews (tuples of rating/text)
    - menu_item: List of menu items
    - listed_in(type): Type of meal (e.g. buffet, delivery)
    - listed_in(city): City category listing
    """
    logger.info("Loading raw dataset from Hugging Face...")
    try:
        # Load dataset
        dataset_dict = datasets.load_dataset("ManikaSaini/zomato-restaurant-recommendation")
        
        # Check available splits
        splits = list(dataset_dict.keys())
        if not splits:
            raise ValueError("No splits found in the loaded dataset dictionary.")
        
        # We use the first split (usually 'train')
        primary_split = "train" if "train" in splits else splits[0]
        dataset = dataset_dict[primary_split]
        
        logger.info(f"Successfully loaded {len(dataset)} raw records from split '{primary_split}'.")
        
        # Convert to list of dicts for portability
        records = [record for record in dataset]
        return records
    except Exception as e:
        logger.exception("Failed to load dataset from Hugging Face Hub")
        raise e
