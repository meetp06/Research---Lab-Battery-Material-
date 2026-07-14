"""
Opti-Battery automated discovery monitor.

A watcher loop that periodically re-screens the Materials Project
(and other sources), compares new candidates against the stored
champion for each spec, and records + notifies whenever a better,
non-toxic material appears.

It surfaces better EXISTING materials as databases grow. It does
not discover new elements, and it does not validate physical cells.
"""
from opti_battery.monitor.scanner import run_scan

__all__ = ["run_scan"]
