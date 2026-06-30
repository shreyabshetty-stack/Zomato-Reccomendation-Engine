import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file at the workspace root
# Find the project root directory
root_dir = Path(__file__).resolve().parent.parent
env_path = root_dir / ".env"

if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

# Groq API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Groq Model (default: llama-3.3-70b-versatile)
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Cache path configuration
dataset_cache = os.getenv("DATASET_CACHE_PATH")
DATASET_CACHE_PATH = Path(dataset_cache) if dataset_cache else None

# Helper functions for integer parsing
def _get_env_int(key: str, default: int) -> int:
    val = os.getenv(key)
    if val is None:
        return default
    try:
        return int(val)
    except ValueError:
        return default

# Candidate thresholds
MAX_CANDIDATES = _get_env_int("MAX_CANDIDATES", 25)
TOP_N = _get_env_int("TOP_N", 5)

# Validate critical API key is present (does not crash on import, but can be checked)
def validate_config() -> bool:
    """Helper to validate configuration at runtime before calls are made."""
    if not GROQ_API_KEY:
        return False
    return True
