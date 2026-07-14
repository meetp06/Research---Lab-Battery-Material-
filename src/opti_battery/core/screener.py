from typing import List, Dict, Any
from opti_battery.core.client import get_mp_rester

def screen_battery_materials(
    exclude_elements: List[str] = None,
    max_density: float = 3.0,
    min_sse_band_gap: float = 2.0,
    limit: int = 5
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Screen stable Lithium materials into Solid-State Electrolytes (SSE) and Electrode candidates.
    
    SSE candidates are electronic insulators (band gap > min_sse_band_gap).
    Electrode candidates are electronic conductors (is_metal or band gap == 0).
    
    Returns:
        Dictionary with keys 'sse' and 'electrodes', each containing lists of candidates.
    """
    if exclude_elements is None:
        exclude_elements = ["Pb", "Cd", "Hg", "As"]
        
    with get_mp_rester() as mpr:
        docs = mpr.materials.summary.search(
            elements=["Li"],
            exclude_elements=exclude_elements,
            density=(0.0, max_density),
            is_stable=True,
            fields=[
                "material_id", 
                "formula_pretty", 
                "density", 
                "symmetry", 
                "band_gap", 
                "is_metal"
            ]
        )
        
        # Partition
        sse_candidates = []
        electrode_candidates = []
        
        for doc in docs:
            system = str(doc.symmetry.crystal_system if doc.symmetry else "Unknown")
            mat_dict = {
                "material_id": str(doc.material_id),
                "formula": str(doc.formula_pretty),
                "density": float(doc.density),
                "band_gap": float(doc.band_gap) if doc.band_gap is not None else 0.0,
                "system": system
            }
            
            if doc.band_gap is not None and doc.band_gap > min_sse_band_gap:
                sse_candidates.append(mat_dict)
            elif doc.is_metal or (doc.band_gap is not None and doc.band_gap == 0.0):
                electrode_candidates.append(mat_dict)
                
        # Sort by density ascending
        sse_sorted = sorted(sse_candidates, key=lambda x: x["density"])
        electrode_sorted = sorted(electrode_candidates, key=lambda x: x["density"])
        
        return {
            "sse": sse_sorted[:limit],
            "electrodes": electrode_sorted[:limit]
        }
