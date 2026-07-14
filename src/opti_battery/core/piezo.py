import os
import json
from pathlib import Path
from typing import List, Dict, Any
from opti_battery.core.client import get_mp_rester

# Local cache for Piezoelectric tensor data
CACHE_FILE = Path(__file__).resolve().parent / "piezo_cache.json"

def _download_and_cache_piezo_data():
    """
    Downloads all materials with a known piezoelectric tensor from the Materials Project,
    extracts the top candidates, and caches them locally to avoid repeated 3,000+ document queries.
    """
    print("Downloading Piezoelectric data from Materials Project... (This will take a few seconds but only happens once)")
    
    with get_mp_rester() as mpr:
        # Search for all materials with piezoelectric data
        docs = mpr.materials.piezoelectric.search()
        
        candidates = []
        for doc in docs:
            # e_ij_max is the maximum piezoelectric modulus in C/m^2
            if doc.e_ij_max is not None:
                candidates.append({
                    "material_id": str(doc.material_id),
                    "formula": str(getattr(doc, "formula_pretty", getattr(doc, "material_id", "Unknown"))),
                    "e_ij_max": float(doc.e_ij_max)
                })
                
        # Sort by maximum piezoelectric response (descending)
        candidates.sort(key=lambda x: x["e_ij_max"], reverse=True)
        
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(candidates, f, indent=2)
            
        print(f"Successfully cached {len(candidates)} piezoelectric materials.")

def get_top_piezo_materials(limit: int = 20) -> List[Dict[str, Any]]:
    """
    Retrieves the top N piezoelectric nanogenerator candidates.
    Uses local cache for instant performance.
    """
    if not CACHE_FILE.exists():
        _download_and_cache_piezo_data()
        
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    return data[:limit]
