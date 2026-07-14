from typing import Dict, Any, List
from pymatgen.core import Composition
from pymatgen.analysis.interface_reactions import InterfacialReactivity
from pymatgen.analysis.phase_diagram import PhaseDiagram
from opti_battery.core.client import get_mp_rester

def calculate_interface_properties(
    reactant1_formula: str,
    reactant2_formula: str
) -> Dict[str, Any]:
    """
    Calculate the interfacial reactivity between two materials.
    
    Returns:
        Dictionary containing stability status, minimum reaction energy (driving force),
        and list of decomposition reactions.
    """
    c1 = Composition(reactant1_formula)
    c2 = Composition(reactant2_formula)
    
    # Construct chemical system (elements of both reactants)
    el1 = [el.symbol for el in c1.elements]
    el2 = [el.symbol for el in c2.elements]
    chemsys = list(set(el1 + el2))
    
    with get_mp_rester() as mpr:
        entries = mpr.get_entries_in_chemsys(chemsys)
        pd = PhaseDiagram(entries)
        
        ir = InterfacialReactivity(c1, c2, pd, norm=True, use_hull_energy=False)
        kinks = ir.get_kinks()
        
        min_energy = min([k[2] for k in kinks])
        reactions = []
        for k in kinks:
            if k[2] < 0:
                reactions.append({
                    "ratio": float(k[0]),
                    "energy": float(k[2]),
                    "reaction": str(k[3])
                })
                
        return {
            "stable": bool(min_energy == 0.0),
            "driving_force": float(min_energy),
            "reactions": reactions
        }

def compute_interface_stability(
    electrolyte_formula: str,
    anode_formula: str,
    cathode_formula: str
) -> Dict[str, Any]:
    """
    Compute stability metrics for both anode and cathode interfaces.
    """
    anode_res = calculate_interface_properties(electrolyte_formula, anode_formula)
    cathode_res = calculate_interface_properties(electrolyte_formula, cathode_formula)
    
    return {
        "anode": anode_res,
        "cathode": cathode_res
    }
