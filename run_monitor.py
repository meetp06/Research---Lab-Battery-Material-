"""
=================================================================
OPTI-BATTERY: Automated Discovery Monitor (cron entrypoint)
=================================================================
Runs one auto-discovery scan: re-screens the Materials Project for
all 5 specs, filters toxic/radioactive candidates, and crowns a new
champion whenever a better KNOWN material appears. Optionally also
mines recent arXiv papers as literature signals.

Designed to be run on a schedule (GitHub Actions / cron):

    python3 run_monitor.py            # DFT re-screen scan
    python3 run_monitor.py --papers   # scan + arXiv literature mining
    python3 run_monitor.py --papers-only

State is written to discovery_state.json (current champions) and
discovery_history.json (append-only feed), both at the project root.
=================================================================
"""
import os
import sys
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from opti_battery.monitor.scanner import run_scan
from opti_battery.monitor.paper_miner import mine_papers


def main():
    parser = argparse.ArgumentParser(description="Opti-Battery auto-discovery monitor")
    parser.add_argument("--papers", action="store_true",
                        help="Also mine recent arXiv papers as literature signals")
    parser.add_argument("--papers-only", action="store_true",
                        help="Skip the DFT re-screen; only mine arXiv papers")
    args = parser.parse_args()

    if args.papers_only:
        mine_papers()
        return

    # Mine + embed papers FIRST so champion verdicts (RAG) have literature
    # context to draw on during the scan.
    if args.papers:
        mine_papers()
    run_scan()


if __name__ == "__main__":
    main()
