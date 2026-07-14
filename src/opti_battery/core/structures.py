from opti_battery.core.client import get_mp_rester

def get_structure_cif(material_id: str) -> str:
    """
    Fetch the structure of a given material ID and convert it to a CIF formatted string.
    
    Args:
        material_id: The Materials Project ID (e.g. 'mp-995393').
        
    Returns:
        CIF formatted string.
    """
    with get_mp_rester() as mpr:
        docs = mpr.materials.summary.search(
            material_ids=[material_id],
            fields=["structure"]
        )
        
        if docs and docs[0].structure:
            structure = docs[0].structure
            # Return string CIF representation
            return structure.to(fmt="cif")
        else:
            raise ValueError(f"Structure not found for material ID: {material_id}")
