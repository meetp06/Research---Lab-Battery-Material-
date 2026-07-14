"""
ML surrogate scaffold (fast pre-screen).

GOAL: replace slow, per-material DFT/geometry work with an instant
ML prediction so the monitor can pre-rank millions of candidates and
only run the expensive screening on the promising top slice. This is
where the user's AI/ML background adds the most leverage.

STATUS: interface scaffold only. A real surrogate needs a trained
model (pretrained universal potentials — CHGNet / MatterSim / M3GNet —
fine-tuned on Materials Project labels) plus heavy deps (torch, etc.),
which is a separate training job, not a one-file drop-in.

Wiring plan:
  1. pip install chgnet   (or mattersim / matgl)
  2. implement predict_stability() / predict_conductivity() below
  3. in scanner.scan_spec, call rank_candidates() to pre-sort a large
     candidate pool BEFORE the exact screening, so DFT-grade work runs
     only on the top slice.
"""
from typing import List, Dict, Any

_MODEL = None


def is_available() -> bool:
    """True once a real surrogate model is loaded. False for the stub."""
    return _MODEL is not None


def load_model():
    """
    Load a pretrained universal potential. Not implemented yet.

    Example (CHGNet):
        from chgnet.model import CHGNet
        global _MODEL
        _MODEL = CHGNet.load()
    """
    raise NotImplementedError(
        "ML surrogate not wired up. Install chgnet/mattersim and implement "
        "load_model() + predict_* to enable fast pre-screening."
    )


def predict_stability(structure) -> float:
    """Predict energy above hull (eV/atom). Lower = more stable."""
    raise NotImplementedError


def rank_candidates(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Pre-rank candidates with the surrogate when available; otherwise
    return them unchanged so the pipeline still works without ML.
    """
    if not is_available():
        return candidates
    # Placeholder: real impl scores each structure and sorts.
    return candidates
