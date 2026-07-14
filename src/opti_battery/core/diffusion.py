from typing import Dict, Any
from opti_battery.core.client import get_mp_rester

def analyze_lithium_diffusion(material_id: str) -> Dict[str, Any]:
    """
    Analyze Lithium-ion diffusion hopping pathways in the crystal structure.
    
    Computes distances between adjacent Lithium sites to evaluate geometric
    hopping barriers and percolation.
    """
    with get_mp_rester() as mpr:
        docs = mpr.materials.summary.search(
            material_ids=[material_id],
            fields=["structure", "formula_pretty"]
        )
        
        if not docs or not docs[0].structure:
            raise ValueError(f"Structure not found for material ID: {material_id}")
            
        structure = docs[0].structure
        
        # Find indices of all Lithium sites in the unit cell
        li_indices = [i for i, site in enumerate(structure.sites) if site.specie.symbol == "Li"]
        
        if len(li_indices) <= 1:
            return {
                "material_id": material_id,
                "formula": docs[0].formula_pretty,
                "li_count": len(li_indices),
                "min_hop": 0.0,
                "avg_hop": 0.0,
                "max_hop": 0.0,
                "connected_3d": False,
                "message": "Too few Lithium sites in the unit cell to establish percolation paths."
            }
            
        # For each Li site, find its closest Lithium neighbors (using 6.0 Å search radius)
        hop_distances = []
        for i in li_indices:
            site = structure[i]
            neighbors = structure.get_neighbors(site, r=6.0)
            # Filter for Lithium neighbors only
            li_neighbors = [n for n in neighbors if n.specie.symbol == "Li"]
            if li_neighbors:
                min_dist = min([n.nn_distance for n in li_neighbors])
                hop_distances.append(min_dist)
                
        if not hop_distances:
            return {
                "material_id": material_id,
                "formula": docs[0].formula_pretty,
                "li_count": len(li_indices),
                "min_hop": 0.0,
                "avg_hop": 0.0,
                "max_hop": 0.0,
                "connected_3d": False,
                "message": "No adjacent Lithium sites found within a 6.0 Å hopping radius."
            }
            
        min_hop = min(hop_distances)
        avg_hop = sum(hop_distances) / len(hop_distances)
        max_hop = max(hop_distances)
        
        # In solid-state physics, a hopping distance < 3.5 Å is considered a low-energy barrier path
        percolates = bool(max_hop <= 3.5)
        
        return {
            "material_id": material_id,
            "formula": docs[0].formula_pretty,
            "li_count": len(li_indices),
            "min_hop": float(min_hop),
            "avg_hop": float(avg_hop),
            "max_hop": float(max_hop),
            "connected_3d": percolates,
            "message": "Excellent 3D diffusion pathways!" if percolates else "Isolated sites or high-barrier hopping pathways (> 3.5 Å) detected."
        }
