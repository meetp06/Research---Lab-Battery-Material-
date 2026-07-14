from typing import List, Dict, Any
from opti_battery.core.client import get_mp_rester

def find_lightweight_lithium_materials(
    exclude_elements: List[str] = None,
    max_density: float = 3.0,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Query the Materials Project database for stable, lightweight Lithium compounds.
    
    Args:
        exclude_elements: List of element symbols to exclude (e.g. ['Pb', 'Cd']).
        max_density: Maximum density in g/cm3.
        limit: Number of results to return.
        
    Returns:
        List of dictionaries with material properties.
    """
    if exclude_elements is None:
        exclude_elements = ["Pb", "Cd"]
        
    with get_mp_rester() as mpr:
        docs = mpr.materials.summary.search(
            elements=["Li"],
            exclude_elements=exclude_elements,
            density=(0.0, max_density),
            fields=["material_id", "formula_pretty", "density", "symmetry"]
        )
        
        # Sort by density ascending
        docs_sorted = sorted(docs, key=lambda x: x.density)
        
        results = []
        for doc in docs_sorted[:limit]:
            results.append({
                "material_id": str(doc.material_id),
                "formula": str(doc.formula_pretty),
                "density": float(doc.density),
                "system": str(doc.symmetry.crystal_system if doc.symmetry else "Unknown")
            })
            
        return results
