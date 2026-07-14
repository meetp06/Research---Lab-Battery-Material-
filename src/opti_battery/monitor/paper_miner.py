"""
Literature signal miner (arXiv).

Polls the free arXiv API for recent papers on solid-state battery
materials and records them as "literature signals" in the discovery
history. No API key required; standard library only.

This is deliberately a SIGNAL, not a champion: papers report
cherry-picked, hard-to-verify lab numbers, so entries are tagged
type="literature" and never overwrite the DFT-screened champions.

Optional next step (LLM extraction): feed each abstract to an LLM to
pull {material, reported_metric, value} into structured rows. Left as
a hook — see extract_claim() below.
"""
from datetime import datetime, timezone
from typing import List, Dict, Any
import urllib.parse
import urllib.request

# Use defusedxml to guard against XXE / billion-laughs attacks in the
# arXiv Atom response. Fall back to stdlib only if defusedxml is absent.
try:
    import defusedxml.ElementTree as ET
except ImportError:  # pragma: no cover
    import xml.etree.ElementTree as ET

from opti_battery.monitor import store, rag, llm
from opti_battery.monitor.notify import notify

ARXIV_API = "http://export.arxiv.org/api/query"
ATOM = "{http://www.w3.org/2005/Atom}"

DEFAULT_QUERY = (
    'all:"solid state battery" OR all:"solid electrolyte" '
    'OR all:"lithium ion conductor"'
)

# Broad, overlapping queries so we cover the whole battery-materials space
# and don't miss papers filed under a different phrasing. Results are merged
# and de-duplicated by arXiv id, so overlap between queries is harmless.
QUERY_SET = [
    'all:"solid state battery" OR all:"solid electrolyte"',
    'all:"lithium ion conductor" OR all:"superionic conductor"',
    'all:"lithium sulfur battery" OR all:"Li-S battery"',
    'all:"garnet electrolyte" OR all:"argyrodite" OR all:"sulfide electrolyte"',
    'all:"cathode material" AND all:"lithium"',
    'all:"anode material" AND all:"lithium"',
    'all:"solid electrolyte interphase" OR all:"dendrite"',
    'all:"machine learning" AND all:"battery material"',
]


def fetch_recent_papers(query: str = DEFAULT_QUERY,
                        max_results: int = 25,
                        start: int = 0) -> List[Dict[str, Any]]:
    """Return recent arXiv papers (newest first) for one query + page."""
    params = urllib.parse.urlencode({
        "search_query": query,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "start": start,
        "max_results": max_results,
    })
    url = f"{ARXIV_API}?{params}"

    with urllib.request.urlopen(url, timeout=30) as resp:
        raw = resp.read()

    root = ET.fromstring(raw)
    papers = []
    for entry in root.findall(f"{ATOM}entry"):
        title = (entry.findtext(f"{ATOM}title") or "").strip().replace("\n", " ")
        summary = (entry.findtext(f"{ATOM}summary") or "").strip().replace("\n", " ")
        published = (entry.findtext(f"{ATOM}published") or "").strip()
        link = (entry.findtext(f"{ATOM}id") or "").strip()
        papers.append({
            "title": title,
            "summary": summary[:500],
            "published": published,
            "url": link,
        })
    return papers


def fetch_broad(per_query: int = 25, pages: int = 1) -> List[Dict[str, Any]]:
    """
    Run the whole QUERY_SET (with optional pagination), merge, and
    de-duplicate by arXiv id so a single scan covers the field broadly.
    A polite delay between calls respects arXiv's rate guidance.
    """
    import time
    seen, merged = set(), []
    for q in QUERY_SET:
        for page in range(pages):
            try:
                batch = fetch_recent_papers(q, max_results=per_query,
                                            start=page * per_query)
            except Exception as e:
                notify(f"  arXiv query failed ({q[:30]}...): {e}")
                continue
            for p in batch:
                if p["url"] and p["url"] not in seen:
                    seen.add(p["url"])
                    merged.append(p)
            time.sleep(3)  # arXiv asks ~3s between requests
    return merged


def mine_papers(per_query: int = 25, pages: int = 1) -> int:
    """
    Broadly fetch recent papers across the full QUERY_SET, LLM-filter for
    relevance, LLM-extract the key claim, embed into the vector store, and
    append new ones to history.

    All LLM/RAG steps degrade gracefully: with no GROQ_API_KEY the
    relevance filter keeps everything and claims stay empty; with no
    chromadb the embedding step is skipped. Either way the feed still works.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    notify(f"📚 arXiv literature scan @ {now_iso} "
           f"(LLM {'on' if llm.is_available() else 'off'}, "
           f"RAG {'on' if rag.is_available() else 'off'})")

    papers = fetch_broad(per_query=per_query, pages=pages)
    if not papers:
        notify("  arXiv returned no papers this scan.")
        return 0

    seen_urls = {h.get("url") for h in store.load_history()
                 if h.get("type") == "literature"}

    added, dropped, kept = 0, 0, []
    for p in papers:
        if p["url"] in seen_urls:
            continue

        # LLM relevance filter (fails open — keeps paper if no model)
        if not llm.is_relevant(p["title"], p["summary"]):
            dropped += 1
            continue

        claim = llm.extract_claim(p["title"], p["summary"])
        store.append_history({
            "timestamp": now_iso,
            "type": "literature",
            "title": p["title"],
            "published": p["published"],
            "url": p["url"],
            "summary": p["summary"],
            "claim": claim,          # {} when nothing extracted
        })
        kept.append(p)
        added += 1

    # Embed the newly kept papers for semantic champion-matching
    embedded = rag.add_papers(kept)

    notify(f"  Added {added} new signal(s), dropped {dropped} off-topic; "
           f"embedded {embedded} into vector store ({len(papers)} fetched).")
    return added
