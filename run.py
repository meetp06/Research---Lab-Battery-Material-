import sys
import argparse
from pathlib import Path

# Add src/ directory to system path to enable modular imports
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from opti_battery.web.server import run_server
from opti_battery.core.miner import find_lightweight_lithium_materials
from opti_battery.core.screener import screen_battery_materials
from opti_battery.core.performance import calculate_electrode_performance
from opti_battery.core.diffusion import analyze_lithium_diffusion
from opti_battery.core.voltage_window import calculate_voltage_window
from opti_battery.core.custom_screener import analyze_custom_cif
from opti_battery.core.piezo import get_top_piezo_materials
from opti_battery.monitor.scanner import run_scan

def run_cli_mine():
    print("Mining Materials Project database for lightweight Lithium candidates...")
    try:
        candidates = find_lightweight_lithium_materials()
        print(f"\nFound {len(candidates)} candidate materials (sorted by density):")
        print("-" * 50)
        for i, c in enumerate(candidates):
            print(f"Rank {i+1}: {c['formula']} ({c['material_id']})")
            print(f"  Density: {c['density']:.2f} g/cm³")
            print(f"  System:  {c['system']}")
            print("-" * 50)
    except Exception as e:
        print(f"Error mining candidates: {str(e)}")
        sys.exit(1)

def run_cli_screen():
    print("Screening Materials Project candidates for Solid-State Electrolytes vs. Electrodes...")
    try:
        results = screen_battery_materials()
        
        print("\n" + "=" * 60)
        print("TOP SOLID-STATE ELECTROLYTE CANDIDATES (Band Gap > 2.0 eV)")
        print("=" * 60)
        for i, c in enumerate(results["sse"]):
            print(f"Rank {i+1}: {c['formula']} ({c['material_id']})")
            print(f"  Density:    {c['density']:.2f} g/cm³")
            print(f"  Band Gap:   {c['band_gap']:.2f} eV")
            print(f"  Symmetry:   {c['system']}")
            print("-" * 40)
            
        print("\n" + "=" * 60)
        print("TOP ELECTRODE CANDIDATES (Conductors)")
        print("=" * 60)
        for i, c in enumerate(results["electrodes"]):
            print(f"Rank {i+1}: {c['formula']} ({c['material_id']})")
            print(f"  Density:    {c['density']:.2f} g/cm³")
            print(f"  Band Gap:   {c['band_gap']:.2f} eV (Conductor)")
            print(f"  Symmetry:   {c['system']}")
            print("-" * 40)
    except Exception as e:
        print(f"Error screening candidates: {str(e)}")
        sys.exit(1)

def run_cli_performance(formula: str):
    print(f"Calculating battery performance metrics for electrode formula: {formula}...")
    try:
        res = calculate_electrode_performance(formula)
        print("\n" + "=" * 50)
        print(f"ELECTRODE PERFORMANCE: {res['formula']}")
        print("=" * 50)
        print(f"Reaction Mechanism Type:  {res['type']}")
        print(f"Working Ion:              {res['working_ion']}")
        print(f"Average Cell Voltage:     {res['average_voltage']:.2f} V vs. Li/Li+")
        print(f"Specific Capacity:        {res['capacity_grav']:.2f} mAh/g")
        print(f"Volumetric Capacity:      {res['capacity_vol']:.2f} Ah/L")
        print(f"Theoretical Specific Energy: {res['capacity_grav'] * res['average_voltage']:.2f} Wh/kg")
        print(f"Max Volume Change:        {res['volume_change']:.2f}%")
        print("=" * 50)
    except Exception as e:
        print(f"Error calculating performance: {str(e)}")
        sys.exit(1)

def run_cli_diffusion(material_id: str):
    print(f"Analyzing Lithium hopping pathway and diffusion percolation for ID: {material_id}...")
    try:
        res = analyze_lithium_diffusion(material_id)
        print("\n" + "=" * 50)
        print(f"LI+ DIFFUSION ANALYSIS: {res['formula']} ({res['material_id']})")
        print("=" * 50)
        print(f"Number of Lithium Sites:  {res['li_count']}")
        print(f"Minimum Hopping Distance: {res['min_hop']:.2f} Å")
        print(f"Average Hopping Distance: {res['avg_hop']:.2f} Å")
        print(f"Maximum Hopping Distance: {res['max_hop']:.2f} Å")
        print(f"Has 3D Connected Path:    {res['connected_3d']}")
        print(f"Remarks:                  {res['message']}")
        print("=" * 50)
    except Exception as e:
        print(f"Error analyzing diffusion: {str(e)}")
        sys.exit(1)

def run_cli_window(formula: str):
    print(f"Calculating electrochemical stability voltage window for electrolyte: {formula}...")
    try:
        res = calculate_voltage_window(formula)
        print("\n" + "=" * 50)
        print(f"ELECTROCHEMICAL WINDOW: {res['formula']}")
        print("=" * 50)
        print(f"Thermodynamic Reduction Limit: {res['reduction_limit']:.2f} V vs. Li/Li+")
        print(f"Thermodynamic Oxidation Limit: {res['oxidation_limit']:.2f} V vs. Li/Li+")
        print("\nPhase Evolution Steps:")
        for step in res["steps"]:
            print(f"  At {step['voltage']:.2f} V: {step['reaction']}")
        print("=" * 50)
    except Exception as e:
        print(f"Error calculating voltage window: {str(e)}")
        sys.exit(1)

def run_cli_analyze_cif(filepath: str):
    print(f"Screening custom CIF structure file: {filepath}...")
    try:
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"CIF file not found: {filepath}")
        with open(path, "r", encoding="utf-8") as f:
            cif_string = f.read()
        res = analyze_custom_cif(cif_string)
        print("\n" + "=" * 50)
        print(f"CUSTOM CIF SCREENING RESULTS: {res['formula']}")
        print("=" * 50)
        print(f"Calculated Density:       {res['density']:.2f} g/cm³")
        print(f"Number of Lithium Sites:  {res['li_count']}")
        print(f"Minimum Hopping Distance: {res['min_hop']:.2f} Å")
        print(f"Average Hopping Distance: {res['avg_hop']:.2f} Å")
        print(f"Maximum Hopping Distance: {res['max_hop']:.2f} Å")
        print(f"Has 3D Connected Path:    {res['connected_3d']}")
        print(f"Remarks:                  {res['message']}")
        print("=" * 50)
    except Exception as e:
        print(f"Error screening CIF file: {str(e)}")
        sys.exit(1)

def run_cli_scan():
    print("Running automated discovery scan (re-screening all 5 specs, "
          "filtering toxic candidates, updating champions)...")
    try:
        report = run_scan()
        print(f"\nScan complete: {report['improved']}/{len(report['reports'])} "
              f"specs improved. See discovery_state.json & discovery_history.json.")
    except Exception as e:
        print(f"Error running discovery scan: {str(e)}")
        sys.exit(1)

def run_cli_piezo():
    print("Querying Materials Project database for Top Piezoelectric Nanogenerator candidates...")
    try:
        candidates = get_top_piezo_materials(limit=20)
        print(f"\nFound {len(candidates)} candidates (sorted by max piezoelectric tensor e_ij):")
        print("-" * 50)
        for i, c in enumerate(candidates):
            print(f"Rank {i+1}: {c['formula']} ({c['material_id']})")
            print(f"  Max Piezo Tensor (e_ij): {c['e_ij_max']:.4f} C/m²")
            print("-" * 50)
    except Exception as e:
        print(f"Error querying piezoelectric candidates: {str(e)}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Opti-Battery Material Discovery Informatics Tool")
    parser.add_argument("--cli", action="store_true", help="Run in Command Line Interface (CLI) mode")
    parser.add_argument("--mine", action="store_true", help="CLI command: Mine lightweight lithium candidate materials")
    parser.add_argument("--screen", action="store_true", help="CLI command: Screen candidates for electrolytes and electrodes")
    parser.add_argument("--performance", type=str, help="CLI command: Calculate battery performance metrics for a given formula (e.g. Li15Si4)")
    parser.add_argument("--diffusion", type=str, help="CLI command: Analyze Lithium hopping pathways for a material ID (e.g. mp-1180666)")
    parser.add_argument("--window", type=str, help="CLI command: Compute electrochemical voltage window for a formula (e.g. Li2BeH4)")
    parser.add_argument("--analyze-cif", type=str, help="CLI command: Screen a custom CIF file for Lithium diffusion pathways")
    parser.add_argument("--piezo", action="store_true", help="CLI command: Query top piezoelectric nanogenerator materials")
    parser.add_argument("--scan", action="store_true", help="CLI command: Run one automated discovery scan (updates champions)")
    parser.add_argument("--port", type=int, default=8085, help="Port to run the web server on (default: 8085)")
    
    args = parser.parse_args()
    
    if args.cli:
        if args.mine:
            run_cli_mine()
        elif args.screen:
            run_cli_screen()
        elif args.performance:
            run_cli_performance(args.performance)
        elif args.diffusion:
            run_cli_diffusion(args.diffusion)
        elif args.window:
            run_cli_window(args.window)
        elif args.analyze_cif:
            # Note: argparse converts dest '--analyze-cif' to 'analyze_cif' in python!
            # Yes, argparse replaces hyphens with underscores!
            run_cli_analyze_cif(args.analyze_cif)
        elif args.piezo:
            run_cli_piezo()
        elif args.scan:
            run_cli_scan()
        else:
            print("Please specify a command (e.g. --mine, --screen, --performance, --diffusion, --window, --analyze-cif, --piezo, or --scan) when running with --cli.")
            sys.exit(1)
    else:
        # Default mode: Start dashboard server
        run_server(port=args.port)

if __name__ == "__main__":
    main()
