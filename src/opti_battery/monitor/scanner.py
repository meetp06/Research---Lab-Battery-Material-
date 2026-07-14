"""
The auto-discovery scan loop.

For each spec:
  1. re-run the SAME screening function used by run_research.py
  2. drop toxic / radioactive candidates (safety filter)
  3. take the best remaining candidate
  4. compare it against the stored champion
  5. if strictly better (or first ever), crown it, log to history, notify

Everything is a computed / DFT-theoretical property of an existing
catalogued material — this loop surfaces better KNOWN materials as the
database grows; it does not discover new elements or validate cells.
"""
from datetime import datetime, timezone
from typing import Dict, Any, List

from opti_battery.core.client import get_mp_rester
from opti_battery.core.research import RESEARCH_FUNCTIONS
from opti_battery.monitor.registry import SPECS
from opti_battery.monitor.filters import filter_safe
from opti_battery.monitor import store, rag, llm
from opti_battery.monitor.notify import notify


def _is_better(spec: Dict[str, Any], candidate: Dict[str, Any],
               champion: Dict[str, Any]) -> bool:
    """True if candidate beats the current champion on the spec metric."""
    if champion is None:
        return True
    metric = spec["metric"]
    new_val = candidate.get(metric)
    old_val = champion.get(metric)
    if new_val is None:
        return False
    if old_val is None:
        return True
    return new_val < old_val if spec["lower_is_better"] else new_val > old_val


def scan_spec(mpr, spec: Dict[str, Any], state: Dict[str, Any],
              now_iso: str) -> Dict[str, Any]:
    """Scan a single spec. Returns a per-spec report dict."""
    key, label, metric, unit = spec["key"], spec["label"], spec["metric"], spec["unit"]

    research_fn = RESEARCH_FUNCTIONS[key]
    raw = research_fn(mpr, top_n=20)
    safe = filter_safe(raw)

    report = {
        "spec": key,
        "label": label,
        "scanned": len(raw),
        "safe": len(safe),
        "improved": False,
        "winner": None,
    }

    if not safe:
        notify(f"  {label}: no safe candidates this scan "
               f"({len(raw)} scanned, all filtered).")
        return report

    best = safe[0]  # research functions already return best-first
    champion = store.get_champion(state, key)

    if _is_better(spec, best, champion):
        old_str = (f"{champion.get(metric)} {unit} ({champion.get('formula')})"
                   if champion else "none yet")

        # RAG: pull semantically related papers, then LLM literature verdict.
        related = rag.related_papers(
            f"{best.get('formula')} {label} lithium battery material", k=5)
        verdict = llm.champion_verdict(label, best, related)
        if verdict:
            best = {**best, "llm_verdict": verdict}
            notify(f"     🧠 {verdict.get('confidence', '?')} confidence: "
                   f"{verdict.get('verdict', '')}")

        store.set_champion(state, key, best)
        rag.add_champion(key, best)
        entry = {
            "timestamp": now_iso,
            "type": "champion",
            "spec": key,
            "label": label,
            "formula": best.get("formula"),
            "material_id": best.get("material_id"),
            "metric": metric,
            "value": best.get(metric),
            "unit": unit,
            "previous": old_str,
            "llm_verdict": verdict or None,
        }
        store.append_history(entry)
        report["improved"] = True
        report["winner"] = entry
        notify(f"  🎉 {label}: NEW CHAMPION {best.get('formula')} "
               f"({best.get('material_id')}) — {best.get(metric)} {unit}. "
               f"Was: {old_str}")
    else:
        cur = champion.get("formula") if champion else "?"
        notify(f"  {label}: no improvement. Champion stays {cur} "
               f"({champion.get(metric)} {unit}).")

    return report


def run_scan() -> Dict[str, Any]:
    """Run a full scan across all specs. Returns a summary report."""
    now_iso = datetime.now(timezone.utc).isoformat()
    notify(f"🔍 Opti-Battery auto-discovery scan @ {now_iso}")

    state = store.load_state()
    reports: List[Dict[str, Any]] = []

    with get_mp_rester() as mpr:
        for spec in SPECS:
            reports.append(scan_spec(mpr, spec, state, now_iso))

    state["last_scan"] = now_iso
    store.save_state(state)

    improved = [r for r in reports if r["improved"]]
    notify(f"✅ Scan complete. {len(improved)}/{len(reports)} specs improved.")

    return {"timestamp": now_iso, "improved": len(improved), "reports": reports}
