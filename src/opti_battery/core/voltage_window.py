from typing import Dict, Any, List
from pymatgen.analysis.phase_diagram import PhaseDiagram
from pymatgen.core import Composition, Element
from opti_battery.core.client import get_mp_rester

def calculate_voltage_window(formula: str) -> Dict[str, Any]:
    """
    Calculate the electrochemical stability voltage window (vs. Li/Li+)
    of a solid-state electrolyte candidate.
    """
    comp = Composition(formula)
    elements = [el.symbol for el in comp.elements]
    
    # Ensure Li is included in the chemical system
    chemsys = list(set(elements + ["Li"]))
    
    with get_mp_rester() as mpr:
        entries = mpr.get_entries_in_chemsys(chemsys)
        pd = PhaseDiagram(entries)
        
        # Reference chemical potential of Li metal
        mu_Li_0 = pd.el_refs[Element("Li")].energy_per_atom
        
        # Calculate the element profile for Li
        profile = pd.get_element_profile(Element("Li"), comp)
        
        steps = []
        for step in profile:
            voltage = -(step["chempot"] - mu_Li_0)
            steps.append({
                "voltage": float(voltage),
                "reaction": str(step["reaction"])
            })
            
        # Sort steps by voltage
        steps_sorted = sorted(steps, key=lambda x: x["voltage"])
        
        # Estimate stability limits
        # Find the voltages where the material begins to decompose
        reduction_limit = 0.0
        oxidation_limit = 3.0
        
        # If there are steps, we can find the range of stable voltages
        # The reduction limit is typically the first reaction step above 0 V
        non_zero_steps = [s for s in steps_sorted if s["voltage"] > 0.01]
        
        if non_zero_steps:
            reduction_limit = non_zero_steps[0]["voltage"]
            oxidation_limit = non_zero_steps[-1]["voltage"]
        else:
            reduction_limit = 0.0
            oxidation_limit = 0.0
            
        return {
            "formula": formula,
            "reduction_limit": float(reduction_limit),
            "oxidation_limit": float(oxidation_limit),
            "steps": steps_sorted
        }
