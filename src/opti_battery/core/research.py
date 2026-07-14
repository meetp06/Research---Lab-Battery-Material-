"""
=================================================================
OPTI-BATTERY: Research Screening Functions (importable core)
=================================================================
The 5 "Insane Specification" screening routines, factored out so
BOTH the one-shot `run_research.py` pipeline AND the automated
`monitor` auto-discovery loop can reuse the exact same logic.

Each research_* function takes an open MPRester (`mpr`) and returns
a list of candidate dicts sorted best-first. NOTHING here is a
lab-measured value — every metric is a computed / DFT-theoretical
property of an existing catalogued `mp-xxxx` material.
=================================================================
"""
from typing import List, Dict, Any


# =====================================================================
# SPEC 1: CHARGING SPEED — fastest lithium-ion conductors (shortest hop)
# =====================================================================
def research_charging_speed(mpr, top_n: int = 20) -> List[Dict[str, Any]]:
    docs = mpr.materials.summary.search(
        elements=["Li"],
        energy_above_hull=(0, 0.025),
        num_elements=(2, 5),
        fields=["material_id", "formula_pretty", "density", "volume",
                "energy_above_hull", "structure", "symmetry"]
    )

    results = []
    for doc in docs:
        try:
            structure = doc.structure
            li_indices = [j for j, site in enumerate(structure) if str(site.specie) == "Li"]
            if len(li_indices) < 2:
                continue

            min_hop = float("inf")
            for a in range(len(li_indices)):
                for b in range(a + 1, len(li_indices)):
                    d = structure.get_distance(li_indices[a], li_indices[b])
                    if 0.5 < d < min_hop:
                        min_hop = d

            if min_hop < 4.0:
                results.append({
                    "material_id": str(doc.material_id),
                    "formula": doc.formula_pretty,
                    "density": round(doc.density, 4),
                    "energy_above_hull": round(doc.energy_above_hull, 6),
                    "min_li_hop_angstrom": round(min_hop, 4),
                    "space_group": doc.symmetry.symbol if doc.symmetry else "N/A",
                    "score_description": "Shorter hop = faster charging",
                })
        except Exception:
            continue

    results.sort(key=lambda x: x["min_li_hop_angstrom"])
    return results[:top_n]


# =====================================================================
# SPEC 2: CAPACITY — highest energy density (Li-S focus)
# =====================================================================
def research_capacity(mpr, top_n: int = 20) -> List[Dict[str, Any]]:
    docs = mpr.materials.summary.search(
        chemsys="Li-S",
        energy_above_hull=(0, 0.1),
        fields=["material_id", "formula_pretty", "density", "volume",
                "energy_above_hull", "formation_energy_per_atom", "structure"]
    )

    results = []

    def _add(doc):
        comp = doc.structure.composition
        li_fraction = comp.get_atomic_fraction("Li")
        s_fraction = comp.get_atomic_fraction("S")
        molar_mass = float(comp.weight) / comp.num_atoms
        capacity_proxy = (li_fraction * 96485) / molar_mass  # mAh/g approx
        results.append({
            "material_id": str(doc.material_id),
            "formula": doc.formula_pretty,
            "density": round(doc.density, 4),
            "energy_above_hull": round(doc.energy_above_hull, 6),
            "formation_energy": round(doc.formation_energy_per_atom, 4),
            "li_fraction": round(li_fraction, 4),
            "s_fraction": round(s_fraction, 4),
            "capacity_proxy_mAh_g": round(capacity_proxy, 2),
            "score_description": "Higher capacity_proxy = more energy",
        })

    for doc in docs:
        try:
            _add(doc)
        except Exception:
            continue

    # Broaden into Li-S-X ternary systems for advanced Li-S candidates
    for extra_element in ["C", "O", "N", "P", "Fe"]:
        try:
            extra_docs = mpr.materials.summary.search(
                chemsys=f"Li-S-{extra_element}",
                energy_above_hull=(0, 0.05),
                fields=["material_id", "formula_pretty", "density",
                        "energy_above_hull", "formation_energy_per_atom", "structure"]
            )
            for doc in extra_docs:
                try:
                    _add(doc)
                except Exception:
                    continue
        except Exception:
            continue

    # Deduplicate by material_id
    seen, unique = set(), []
    for r in results:
        if r["material_id"] not in seen:
            seen.add(r["material_id"])
            unique.append(r)

    unique.sort(key=lambda x: x["capacity_proxy_mAh_g"], reverse=True)
    return unique[:top_n]


# =====================================================================
# SPEC 3: LIFESPAN — most thermodynamically stable insulating electrolytes
# =====================================================================
def research_lifespan(mpr, top_n: int = 20) -> List[Dict[str, Any]]:
    docs = mpr.materials.summary.search(
        elements=["Li"],
        energy_above_hull=(0, 0.0),
        num_elements=(3, 5),
        fields=["material_id", "formula_pretty", "density",
                "energy_above_hull", "formation_energy_per_atom",
                "band_gap", "symmetry"]
    )

    results = []
    for doc in docs:
        try:
            bg = doc.band_gap if doc.band_gap else 0
            if bg < 1.0:
                continue  # electrolytes must be electronic insulators
            results.append({
                "material_id": str(doc.material_id),
                "formula": doc.formula_pretty,
                "density": round(doc.density, 4),
                "formation_energy": round(doc.formation_energy_per_atom, 4),
                "band_gap_eV": round(bg, 4),
                "space_group": doc.symmetry.symbol if doc.symmetry else "N/A",
                "score_description": "More negative formation energy = harder to decompose",
            })
        except Exception:
            continue

    results.sort(key=lambda x: x["formation_energy"])
    return results[:top_n]


# =====================================================================
# SPEC 4: FORM FACTOR — lightest / lowest-density Li materials
# =====================================================================
def research_form_factor(mpr, top_n: int = 20) -> List[Dict[str, Any]]:
    docs = mpr.materials.summary.search(
        elements=["Li"],
        energy_above_hull=(0, 0.05),
        density=(0, 2.0),
        fields=["material_id", "formula_pretty", "density", "volume",
                "energy_above_hull", "formation_energy_per_atom",
                "band_gap", "symmetry"]
    )

    results = []
    for doc in docs:
        try:
            results.append({
                "material_id": str(doc.material_id),
                "formula": doc.formula_pretty,
                "density_g_cm3": round(doc.density, 4),
                "volume_A3": round(doc.volume, 2),
                "energy_above_hull": round(doc.energy_above_hull, 6),
                "band_gap_eV": round(doc.band_gap, 4) if doc.band_gap else 0,
                "space_group": doc.symmetry.symbol if doc.symmetry else "N/A",
                "score_description": "Lower density = lighter & thinner battery",
            })
        except Exception:
            continue

    results.sort(key=lambda x: x["density_g_cm3"])
    return results[:top_n]


# =====================================================================
# SPEC 5: DURABILITY — mechanically strongest Li materials
# =====================================================================
def research_durability(mpr, top_n: int = 20) -> List[Dict[str, Any]]:
    docs = mpr.materials.summary.search(
        elements=["Li"],
        energy_above_hull=(0, 0.05),
        has_props=["elasticity"],
        fields=["material_id", "formula_pretty", "density",
                "bulk_modulus", "shear_modulus", "symmetry"]
    )

    results = []
    for doc in docs:
        try:
            bulk, shear = doc.bulk_modulus, doc.shear_modulus
            if bulk is None or shear is None:
                continue
            bulk_val = bulk.get("vrh", 0) if isinstance(bulk, dict) else float(bulk)
            shear_val = shear.get("vrh", 0) if isinstance(shear, dict) else float(shear)
            results.append({
                "material_id": str(doc.material_id),
                "formula": doc.formula_pretty,
                "bulk_modulus_GPa": round(bulk_val, 2),
                "shear_modulus_GPa": round(shear_val, 2),
                "strength_score": round(bulk_val + shear_val, 2),
                "density": round(doc.density, 4) if doc.density else 0,
                "space_group": doc.symmetry.symbol if doc.symmetry else "N/A",
                "score_description": "Higher bulk+shear modulus = more durable",
            })
        except Exception:
            continue

    results.sort(key=lambda x: x["strength_score"], reverse=True)
    return results[:top_n]


# Registry consumed by run_research.py and the monitor scanner.
# Each entry: research callable, the metric key in the returned dicts,
# and whether "lower is better".
RESEARCH_FUNCTIONS = {
    "charging_speed": research_charging_speed,
    "capacity": research_capacity,
    "lifespan": research_lifespan,
    "form_factor": research_form_factor,
    "durability": research_durability,
}
