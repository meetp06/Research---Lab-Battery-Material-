"""
Persistence for the auto-discovery monitor.

Two JSON files at the project root:
  - discovery_state.json   : current champion per spec + last_scan timestamp
  - discovery_history.json : append-only log of every new champion crowned
                             and any literature signals from the paper miner

Timestamps are passed IN by the caller (the runtime forbids Date.now()-style
calls inside some contexts), so this module never generates time itself.
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional

ROOT = Path(__file__).resolve().parents[3]
STATE_FILE = ROOT / "discovery_state.json"
HISTORY_FILE = ROOT / "discovery_history.json"


def _load(path: Path, default):
    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _save(path: Path, data) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_state() -> Dict[str, Any]:
    """{'champions': {spec_key: candidate}, 'last_scan': iso_str|None}"""
    return _load(STATE_FILE, {"champions": {}, "last_scan": None})


def save_state(state: Dict[str, Any]) -> None:
    _save(STATE_FILE, state)


def load_history() -> list:
    return _load(HISTORY_FILE, [])


def append_history(entry: Dict[str, Any]) -> None:
    history = load_history()
    history.insert(0, entry)  # newest first
    _save(HISTORY_FILE, history)


def get_champion(state: Dict[str, Any], spec_key: str) -> Optional[Dict[str, Any]]:
    return state.get("champions", {}).get(spec_key)


def set_champion(state: Dict[str, Any], spec_key: str, candidate: Dict[str, Any]) -> None:
    state.setdefault("champions", {})[spec_key] = candidate
