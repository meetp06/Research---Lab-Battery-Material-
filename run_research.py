"""
=================================================================
OPTI-BATTERY: Full Research Pipeline (one-shot)
=================================================================
Queries the Materials Project API for candidate materials across
all 5 "Insane Specifications" and writes research_results.json.

The screening logic lives in `opti_battery.core.research` so the
automated `monitor` auto-discovery loop reuses the EXACT same code.
Every metric is a computed / DFT-theoretical value — not a
lab-measured battery cell.
=================================================================
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from opti_battery.core.client import get_mp_rester
from opti_battery.core.research import (
    research_charging_speed,
    research_capacity,
    research_lifespan,
    research_form_factor,
    research_durability,
)

RESULTS_FILE = "research_results.json"


def run_full_research():
    print("=" * 65)
    print("  OPTI-BATTERY FULL RESEARCH PIPELINE")
    print("  Mining Materials Project for ALL 5 Specifications")
    print("=" * 65)

    all_results = {}
    with get_mp_rester() as mpr:
        print("\n⚡ SPEC 1: CHARGING SPEED — fastest Li-ion conductors...")
        all_results["charging_speed"] = research_charging_speed(mpr)
        print("\n🔋 SPEC 2: CAPACITY — Li-S high energy density...")
        all_results["capacity"] = research_capacity(mpr)
        print("\n♻️ SPEC 3: LIFESPAN — ultra-stable electrolytes...")
        all_results["lifespan"] = research_lifespan(mpr)
        print("\n📐 SPEC 4: FORM FACTOR — lightest Li materials...")
        all_results["form_factor"] = research_form_factor(mpr)
        print("\n🛡️ SPEC 5: DURABILITY — mechanically strongest Li materials...")
        all_results["durability"] = research_durability(mpr)

    with open(RESULTS_FILE, "w") as f:
        json.dump(all_results, f, indent=2)

    print("\n")
    print("=" * 65)
    print("  RESEARCH COMPLETE — SUMMARY REPORT")
    print("=" * 65)

    specs = [
        ("⚡ CHARGING SPEED", "charging_speed", "min_li_hop_angstrom", "Å hop"),
        ("🔋 CAPACITY", "capacity", "capacity_proxy_mAh_g", "mAh/g"),
        ("♻️ LIFESPAN", "lifespan", "formation_energy", "eV/atom"),
        ("📐 FORM FACTOR", "form_factor", "density_g_cm3", "g/cm³"),
        ("🛡️ DURABILITY", "durability", "strength_score", "GPa"),
    ]

    for label, key, metric, unit in specs:
        data = all_results[key]
        print(f"\n{label} — Top 5:")
        print(f"  {'Rank':<5} {'Formula':<20} {'Material ID':<15} {metric:<25} ")
        print(f"  {'-'*5} {'-'*20} {'-'*15} {'-'*25}")
        for i, item in enumerate(data[:5], 1):
            val = item.get(metric, "N/A")
            print(f"  {i:<5} {item['formula']:<20} {item['material_id']:<15} {val} {unit}")

    print(f"\n\n📁 Full results saved to: {RESULTS_FILE}")
    print(f"   Total candidates found: {sum(len(v) for v in all_results.values())}")
    print("=" * 65)
    return all_results


if __name__ == "__main__":
    run_full_research()
