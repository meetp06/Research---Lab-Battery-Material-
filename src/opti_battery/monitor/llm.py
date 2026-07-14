"""
Groq LLM wrapper for the discovery monitor.

Three cheap jobs, all optional — if GROQ_API_KEY is not set (or the
groq package is missing), every function returns a safe fallback so the
whole pipeline keeps working with zero LLM:

  1. is_relevant()   — filter off-topic arXiv papers (kills the
                       "supercapacitor" keyword-search noise)
  2. extract_claim() — pull {material, metric, value} from an abstract
  3. champion_verdict() — plain-language "does literature back this
                       DFT winner?" summary + confidence, given RAG context

Model is configurable via GROQ_MODEL (default: llama-3.3-70b-versatile).
Nothing here is ground truth — LLM output is a helpful summary layered
on top of DFT numbers and cherry-picked papers.
"""
import os
import json
from typing import Dict, Any, List, Optional

DEFAULT_MODEL = "llama-3.3-70b-versatile"

_client = None
_checked = False


def _get_client():
    """Lazily build a Groq client. Returns None if unavailable."""
    global _client, _checked
    if _checked:
        return _client
    _checked = True
    key = os.getenv("GROQ_API_KEY")
    if not key:
        return None
    try:
        from groq import Groq
        _client = Groq(api_key=key)
    except Exception:
        _client = None
    return _client


def is_available() -> bool:
    return _get_client() is not None


def _chat(prompt: str, system: str = "", json_mode: bool = False,
          max_tokens: int = 512) -> Optional[str]:
    """Single-turn chat. Returns text, or None on any failure."""
    client = _get_client()
    if client is None:
        return None
    model = os.getenv("GROQ_MODEL", DEFAULT_MODEL)
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    try:
        kwargs = {"model": model, "messages": messages,
                  "temperature": 0.2, "max_tokens": max_tokens}
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        resp = client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content
    except Exception as e:
        print(f"  (LLM call failed: {e})")
        return None


def _parse_json(text: Optional[str]) -> Dict[str, Any]:
    if not text:
        return {}
    try:
        return json.loads(text)
    except Exception:
        # try to salvage a JSON object embedded in prose
        start, end = text.find("{"), text.rfind("}")
        if 0 <= start < end:
            try:
                return json.loads(text[start:end + 1])
            except Exception:
                return {}
        return {}


# ---------------------------------------------------------------------------
# Job 1: relevance filter
# ---------------------------------------------------------------------------
def is_relevant(title: str, summary: str) -> bool:
    """
    True if the paper is about solid-state / lithium battery MATERIALS.
    Falls back to True (keep) when the LLM is unavailable — never silently
    drops papers without a model to judge.
    """
    out = _chat(
        prompt=(f"Title: {title}\n\nAbstract: {summary}\n\n"
                "Is this paper primarily about solid-state battery or "
                "lithium-ion battery MATERIALS (electrolytes, electrodes, "
                "ion conductors)? Answer strictly as JSON: "
                '{\"relevant\": true|false}'),
        system="You are a materials-science literature triage assistant.",
        json_mode=True, max_tokens=50,
    )
    data = _parse_json(out)
    if "relevant" not in data:
        return True  # fail open when no model
    return bool(data["relevant"])


# ---------------------------------------------------------------------------
# Job 2: claim extraction
# ---------------------------------------------------------------------------
def extract_claim(title: str, summary: str) -> Dict[str, Any]:
    """
    Extract a reported material + metric + value from an abstract.
    Returns {} when nothing clear or when the LLM is unavailable.
    """
    out = _chat(
        prompt=(f"Title: {title}\n\nAbstract: {summary}\n\n"
                "Extract the single most important reported battery-material "
                "result. Reply strictly as JSON with keys material, metric, "
                "value, unit. Use null for any field you cannot find. "
                'Example: {\"material\":\"Li6PS5Cl\",\"metric\":\"ionic '
                'conductivity\",\"value\":\"12\",\"unit\":\"mS/cm\"}'),
        system="You extract structured claims from scientific abstracts.",
        json_mode=True, max_tokens=200,
    )
    data = _parse_json(out)
    if not data or not data.get("material"):
        return {}
    return data


# ---------------------------------------------------------------------------
# Job 3: champion verdict (RAG)
# ---------------------------------------------------------------------------
def champion_verdict(spec_label: str, champion: Dict[str, Any],
                     related_papers: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Given a newly crowned DFT champion and semantically related papers,
    produce a short literature-evidence verdict. Returns {} when the LLM
    is unavailable.
    """
    formula = champion.get("formula", "?")
    context = "\n".join(
        f"- {p.get('title', '')}" for p in related_papers[:5]
    ) or "(no related papers found in the local vector store)"

    out = _chat(
        prompt=(f"A materials-screening pipeline just ranked {formula} as the "
                f"top candidate for '{spec_label}', based on a computed (DFT) "
                f"property.\n\nRelated papers from our library:\n{context}\n\n"
                "In 2-3 sentences, say whether the literature broadly supports "
                f"{formula} for this use, note any caveat, and give a "
                "confidence in {low, medium, high}. Reply strictly as JSON: "
                '{\"verdict\": \"...\", \"confidence\": \"low|medium|high\"}'),
        system="You are a cautious battery-materials research analyst. "
               "Never overstate; DFT rank is not experimental proof.",
        json_mode=True, max_tokens=300,
    )
    data = _parse_json(out)
    if not data.get("verdict"):
        return {}
    return {
        "verdict": data.get("verdict"),
        "confidence": data.get("confidence", "low"),
        "sources": [p.get("url") for p in related_papers[:5] if p.get("url")],
    }
