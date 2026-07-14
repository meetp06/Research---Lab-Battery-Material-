from typing import Dict, Any
from pymatgen.core import Structure

def analyze_custom_cif(cif_string: str) -> Dict[str, Any]:
    """
    Parse a raw CIF string and analyze its physical characteristics
    and Lithium-ion diffusion hopping pathways on the fly.
    """
    try:
        # Parse the CIF string into a pymatgen Structure object
        structure = Structure.from_str(cif_string, fmt="cif")
    except Exception as e:
        raise ValueError(f"Failed to parse CIF string: {str(e)}")
        
    formula = structure.composition.reduced_formula
    density = structure.density
    
    # Identify indices of all Lithium sites in the structure
    li_indices = [i for i, site in enumerate(structure.sites) if site.specie.symbol == "Li"]
    
    if len(li_indices) <= 1:
        return {
            "formula": formula,
            "density": float(density),
            "li_count": len(li_indices),
            "min_hop": 0.0,
            "avg_hop": 0.0,
            "max_hop": 0.0,
            "connected_3d": False,
            "message": "Too few Lithium sites in the unit cell to establish percolation paths."
        }
        
    # Compute Lithium site-to-site hopping distances
    hop_distances = []
    for i in li_indices:
        site = structure[i]
        neighbors = structure.get_neighbors(site, r=6.0)
        li_neighbors = [n for n in neighbors if n.specie.symbol == "Li"]
        if li_neighbors:
            min_dist = min([n.nn_distance for n in li_neighbors])
            hop_distances.append(min_dist)
            
    if not hop_distances:
        return {
            "formula": formula,
            "density": float(density),
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
    
    # A hopping distance of <= 3.5 Å indicates low activation barrier for Li+ transport
    percolates = bool(max_hop <= 3.5)
    
    return {
        "formula": formula,
        "density": float(density),
        "li_count": len(li_indices),
        "min_hop": float(min_hop),
        "avg_hop": float(avg_hop),
        "max_hop": float(max_hop),
        "connected_3d": percolates,
        "message": "Excellent 3D diffusion pathways!" if percolates else "Isolated sites or high-barrier hopping pathways (> 3.5 Å) detected."
    }
