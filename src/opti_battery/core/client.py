from mp_api.client import MPRester
from opti_battery.config import get_api_key

def get_mp_rester() -> MPRester:
    """Initialize and return a validated MPRester client."""
    api_key = get_api_key()
    return MPRester(api_key=api_key)
