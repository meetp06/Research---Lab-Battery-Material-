import os
import json
from pathlib import Path
from typing import Dict, Any
from pymatgen.core import Composition
from opti_battery.core.client import get_mp_rester

CACHE_PATH = Path(__file__).resolve().parent / "conversion_electrodes_cache.json"

def calculate_electrode_performance(formula: str) -> Dict[str, Any]:
    """
    Retrieve battery performance metrics for a given electrode formula.
    
    Checks insertion_electrodes first. If not found, falls back to a locally
    cached conversion_electrodes database.
    """
    comp = Composition(formula)
    clean_formula = comp.reduced_formula
    
    # Special Case: Pure Lithium Metal Anode
    if clean_formula == "Li":
        return {
            "formula": "Li",
            "type": "Alloying/Stripping Anode",
            "average_voltage": 0.0,
            "capacity_grav": 3861.0,  # mAh/g
            "capacity_vol": 2061.0,   # Ah/L
            "energy_grav": 0.0,
            "energy_vol": 0.0,
            "volume_change": 0.0,     # Negligible in flat representation
            "working_ion": "Li"
        }
        
    # Extract the host framework (all elements except Li)
    host_elements = [el.symbol for el in comp.elements if el.symbol != "Li"]
    if not host_elements:
        host_formula = clean_formula
    else:
        host_comp = Composition({el: comp[el] for el in host_elements})
        host_formula = host_comp.reduced_formula
        
    with get_mp_rester() as mpr:
        # 1. Try Insertion Electrodes first (fast and supports server-side formula filtering)
        docs = mpr.materials.insertion_electrodes.search(formula=host_formula, working_ion="Li")
        if docs:
            # Sort by highest gravimetric capacity
            doc = max(docs, key=lambda x: getattr(x, "capacity_grav", 0.0))
            vol_change = getattr(doc, "max_delta_volume", 0.0)
            if vol_change is None:
                vol_change = 0.0
                
            return {
                "formula": str(doc.battery_formula),
                "type": "Insertion",
                "average_voltage": float(doc.average_voltage) if doc.average_voltage is not None else 0.0,
                "capacity_grav": float(doc.capacity_grav) if doc.capacity_grav is not None else 0.0,
                "capacity_vol": float(doc.capacity_vol) if doc.capacity_vol is not None else 0.0,
                "energy_grav": float(doc.energy_grav) if doc.energy_grav is not None else 0.0,
                "energy_vol": float(doc.energy_vol) if doc.energy_vol is not None else 0.0,
                "volume_change": float(vol_change * 100.0),
                "working_ion": str(doc.working_ion)
            }
            
        # 2. Try Conversion Electrodes (using local cache file to avoid slow page-by-page queries)
        conversion_docs = []
        if os.path.exists(CACHE_PATH):
            try:
                # If cache is old/huge (like the 350MB old cache), let's recreate it
                if os.path.getsize(CACHE_PATH) > 10 * 1024 * 1024:
                    print("Removing large deprecated cache file...")
                    os.remove(CACHE_PATH)
                else:
                    with open(CACHE_PATH, "r") as f:
                        conversion_docs = json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load conversion cache: {str(e)}")
                
        if not conversion_docs:
            print("Downloading conversion electrodes database to local cache (one-time setup)...")
            try:
                # Query all conversion electrodes for Li working ion
                raw_docs = mpr.materials.conversion_electrodes.search(working_ion="Li")
                
                # Simplify to keep cache file extremely small (< 1 MB) and super fast to load
                simplified_docs = []
                for d in raw_docs:
                    vol_change = getattr(d, "max_delta_volume", 0.0)
                    if vol_change is None:
                        vol_change = 0.0
                    simplified_docs.append({
                        "battery_formula": str(d.battery_formula) if hasattr(d, "battery_formula") else None,
                        "capacity_grav": float(d.capacity_grav) if getattr(d, "capacity_grav", None) is not None else 0.0,
                        "capacity_vol": float(d.capacity_vol) if getattr(d, "capacity_vol", None) is not None else 0.0,
                        "average_voltage": float(d.average_voltage) if getattr(d, "average_voltage", None) is not None else 0.0,
                        "max_delta_volume": float(vol_change),
                        "energy_grav": float(d.energy_grav) if getattr(d, "energy_grav", None) is not None else 0.0,
                        "energy_vol": float(d.energy_vol) if getattr(d, "energy_vol", None) is not None else 0.0,
                        "working_ion": str(d.working_ion) if hasattr(d, "working_ion") else "Li",
                        "framework_formula": str(d.framework_formula) if hasattr(d, "framework_formula") else None,
                        "initial_comp_formula": str(d.initial_comp_formula) if hasattr(d, "initial_comp_formula") else None
                    })
                    
                with open(CACHE_PATH, "w") as f:
                    json.dump(simplified_docs, f)
                conversion_docs = simplified_docs
            except Exception as e:
                print(f"Warning: Failed to build conversion cache: {str(e)}")
                
        # Filter conversion documents locally
        matched_convs = []
        for doc in conversion_docs:
            fw_form = doc.get("framework_formula")
            init_form = doc.get("initial_comp_formula")
            if fw_form == host_formula or init_form == host_formula:
                matched_convs.append(doc)
                
        if matched_convs:
            doc = max(matched_convs, key=lambda x: x.get("capacity_grav", 0.0))
            return {
                "formula": str(doc.get("battery_formula")),
                "type": "Conversion",
                "average_voltage": float(doc.get("average_voltage", 0.0)),
                "capacity_grav": float(doc.get("capacity_grav", 0.0)),
                "capacity_vol": float(doc.get("capacity_vol", 0.0)),
                "energy_grav": float(doc.get("energy_grav", 0.0)),
                "energy_vol": float(doc.get("energy_vol", 0.0)),
                "volume_change": float(doc.get("max_delta_volume", 0.0) * 100.0),
                "working_ion": str(doc.get("working_ion", "Li"))
            }
            
        # Fallback dummy calculation if no precomputed data exists
        return {
            "formula": clean_formula,
            "type": "Unknown (No MP precomputed battery data found)",
            "average_voltage": 1.5,
            "capacity_grav": 150.0,
            "capacity_vol": 300.0,
            "energy_grav": 225.0,
            "energy_vol": 450.0,
            "volume_change": 5.0,
            "working_ion": "Li"
        }
