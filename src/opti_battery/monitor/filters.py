"""
Safety filtering for discovered candidates.

Rejects any material containing a radioactive or acutely toxic element
so the auto-discovery loop never crowns an unshippable "winner".
"""
from typing import Tuple
from pymatgen.core import Composition

from opti_battery.monitor.registry import BANNED_ELEMENTS


def toxicity_check(formula: str) -> Tuple[bool, str]:
    """
    Return (is_safe, reason).

    is_safe == False if the formula contains any banned element.
    Unparseable formulas are treated as unsafe (fail closed).
    """
    try:
        elements = {str(el) for el in Composition(formula).elements}
    except Exception:
        return False, f"Unparseable formula '{formula}'"

    hits = sorted(elements & BANNED_ELEMENTS)
    if hits:
        return False, f"Contains banned element(s): {', '.join(hits)}"
    return True, "ok"


def filter_safe(candidates):
    """Keep only candidates that pass the toxicity check (order preserved)."""
    safe = []
    for c in candidates:
        ok, _ = toxicity_check(c.get("formula", ""))
        if ok:
            safe.append(c)
    return safe
