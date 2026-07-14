"""
Project chatbot (RAG over Opti-Battery's own data).

Answers questions about THIS project and its research by retrieving from:
  - the vector "knowledge" collection (champions, research_results,
    RESEARCH.md notes) — see reindex_knowledge()
  - the "papers" collection (arXiv abstracts already embedded by the miner)

then asking Groq to answer grounded ONLY in that context. Degrades
gracefully: no GROQ_API_KEY → returns a clear "LLM offline" message;
no chromadb → answers from live JSON files without semantic retrieval.
"""
import json
from pathlib import Path
from typing import Dict, Any, List

from opti_battery.monitor import rag, llm, store

ROOT = Path(__file__).resolve().parents[3]
RESEARCH_MD = ROOT / "RESEARCH.md"
RESULTS_JSON = ROOT / "research_results.json"


def _chunk_text(text: str, source: str, size: int = 900) -> List[Dict[str, Any]]:
    """Split a long doc into overlapping-ish chunks for indexing."""
    text = text.strip()
    chunks, i, n = [], 0, 0
    while i < len(text):
        chunks.append({"id": f"{source}:{n}",
                       "text": text[i:i + size],
                       "source": source})
        i += size
        n += 1
    return chunks


def reindex_knowledge() -> int:
    """
    (Re)build the knowledge collection from current project state:
    champions, top research_results, and RESEARCH.md. Safe to call often.
    """
    items: List[Dict[str, Any]] = []

    # Champions
    state = store.load_state()
    for spec, champ in (state.get("champions") or {}).items():
        verdict = champ.get("llm_verdict") or {}
        items.append({
            "id": f"champion:{spec}",
            "source": "champion",
            "text": (f"Current champion for {spec}: {champ.get('formula')} "
                     f"({champ.get('material_id')}). "
                     f"Literature verdict: {verdict.get('confidence', 'n/a')} "
                     f"confidence — {verdict.get('verdict', 'none')}"),
        })

    # Top research_results (a few per spec)
    if RESULTS_JSON.exists():
        try:
            data = json.loads(RESULTS_JSON.read_text())
            for spec, rows in data.items():
                for r in rows[:3]:
                    items.append({
                        "id": f"result:{spec}:{r.get('material_id')}",
                        "source": "research_results",
                        "text": (f"{spec} candidate {r.get('formula')} "
                                 f"({r.get('material_id')}): "
                                 + ", ".join(f"{k}={v}" for k, v in r.items()
                                             if k not in ("formula", "material_id"))),
                    })
        except Exception:
            pass

    # RESEARCH.md (our own notes / contribution)
    if RESEARCH_MD.exists():
        items.extend(_chunk_text(RESEARCH_MD.read_text(), "RESEARCH.md"))

    return rag.index_knowledge(items)


def _fallback_context() -> str:
    """Plain-text project context when the vector store is unavailable."""
    lines = []
    state = store.load_state()
    for spec, champ in (state.get("champions") or {}).items():
        lines.append(f"- {spec}: {champ.get('formula')} ({champ.get('material_id')})")
    if RESEARCH_MD.exists():
        lines.append("\nRESEARCH.md:\n" + RESEARCH_MD.read_text()[:2000])
    return "\n".join(lines)


SYSTEM = (
    "You are the Opti-Battery project assistant. Answer questions about this "
    "solid-state battery materials project using ONLY the provided context. "
    "Be accurate and cautious: the materials are existing Materials Project "
    "entries and all metrics are computed/DFT values, not lab-measured cells — "
    "never claim a new element was discovered or a battery was built. If the "
    "context does not contain the answer, say so plainly."
)


def answer(question: str) -> Dict[str, Any]:
    """Answer a question about the project. Returns {answer, sources}."""
    if not llm.is_available():
        return {"answer": "The chatbot needs a GROQ_API_KEY to run. Add one to "
                          ".env (free at console.groq.com) and restart.",
                "sources": []}

    # Ensure knowledge is indexed at least once (cheap upsert if already there).
    try:
        reindex_knowledge()
    except Exception:
        pass

    knowledge = rag.related_knowledge(question, k=6)
    papers = rag.related_papers(question, k=4)

    if knowledge:
        ctx = "\n".join(f"[{k['source']}] {k['text']}" for k in knowledge)
    else:
        ctx = _fallback_context()
    if papers:
        ctx += "\n\nRelated papers:\n" + "\n".join(
            f"- {p['title']}" for p in papers)

    from opti_battery.monitor.llm import _chat  # reuse the Groq helper
    out = _chat(
        prompt=f"Context:\n{ctx}\n\nQuestion: {question}\n\nAnswer:",
        system=SYSTEM, max_tokens=600,
    )
    return {
        "answer": out or "Sorry, I could not generate an answer.",
        "sources": [p["url"] for p in papers if p.get("url")],
    }
