"""
Vector store (semantic memory) for the discovery monitor.

Uses ChromaDB (local, persistent) with sentence-transformers embeddings
(all-MiniLM-L6-v2) — both free, no API key. Two collections:

  - "papers"     : arXiv abstracts, so a new champion can be matched to
                   related literature by MEANING (not keywords)
  - "champions"  : crowned materials, for later similarity search

Everything degrades gracefully: if chromadb / sentence-transformers are
missing, the functions no-op and the scan still runs without RAG.

The DB lives at <project_root>/chroma_db/.
"""
from pathlib import Path
from typing import List, Dict, Any

ROOT = Path(__file__).resolve().parents[3]
DB_DIR = ROOT / "chroma_db"
EMBED_MODEL = "all-MiniLM-L6-v2"

_client = None
_embed_fn = None
_checked = False


def _init():
    """Lazily build the Chroma client + embedding fn. Returns bool ok."""
    global _client, _embed_fn, _checked
    if _checked:
        return _client is not None
    _checked = True
    try:
        import chromadb
        from chromadb.utils import embedding_functions
        _embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBED_MODEL
        )
        _client = chromadb.PersistentClient(path=str(DB_DIR))
    except Exception as e:
        print(f"  (RAG unavailable, continuing without vector store: {e})")
        _client = None
    return _client is not None


def is_available() -> bool:
    return _init()


def _collection(name: str):
    return _client.get_or_create_collection(name=name, embedding_function=_embed_fn)


def add_papers(papers: List[Dict[str, Any]]) -> int:
    """Embed + store arXiv papers (idempotent by url id). Returns count added."""
    if not _init() or not papers:
        return 0
    col = _collection("papers")
    ids, docs, metas = [], [], []
    for p in papers:
        pid = p.get("url")
        if not pid:
            continue
        ids.append(pid)
        docs.append(f"{p.get('title', '')}. {p.get('summary', '')}")
        metas.append({"title": p.get("title", ""),
                      "url": p.get("url", ""),
                      "published": p.get("published", "")})
    if not ids:
        return 0
    # upsert avoids duplicate-id errors across scans
    col.upsert(ids=ids, documents=docs, metadatas=metas)
    return len(ids)


def add_champion(spec_key: str, champion: Dict[str, Any]) -> None:
    """Store a crowned champion for later similarity search."""
    if not _init():
        return
    col = _collection("champions")
    mid = champion.get("material_id", spec_key)
    col.upsert(
        ids=[f"{spec_key}:{mid}"],
        documents=[f"{champion.get('formula', '')} — champion for {spec_key}"],
        metadatas=[{"spec": spec_key,
                    "formula": champion.get("formula", ""),
                    "material_id": mid}],
    )


def related_papers(query_text: str, k: int = 5) -> List[Dict[str, Any]]:
    """Return up to k papers most semantically similar to query_text."""
    if not _init():
        return []
    col = _collection("papers")
    try:
        if col.count() == 0:
            return []
        res = col.query(query_texts=[query_text], n_results=min(k, col.count()))
    except Exception:
        return []
    metas = (res.get("metadatas") or [[]])[0]
    return [{"title": m.get("title"), "url": m.get("url"),
             "published": m.get("published")} for m in metas]


# ---------------------------------------------------------------------------
# Knowledge collection — project facts the chatbot answers from
# ---------------------------------------------------------------------------
def index_knowledge(items: List[Dict[str, Any]]) -> int:
    """
    Upsert project-knowledge chunks. Each item: {id, text, source}.
    Used by the chatbot so it can answer about champions, results, and
    our RESEARCH.md notes. Returns count indexed.
    """
    if not _init() or not items:
        return 0
    col = _collection("knowledge")
    ids = [it["id"] for it in items]
    docs = [it["text"] for it in items]
    metas = [{"source": it.get("source", "")} for it in items]
    col.upsert(ids=ids, documents=docs, metadatas=metas)
    return len(ids)


def related_knowledge(query_text: str, k: int = 6) -> List[Dict[str, Any]]:
    """Return up to k knowledge chunks most similar to query_text."""
    if not _init():
        return []
    col = _collection("knowledge")
    try:
        if col.count() == 0:
            return []
        res = col.query(query_texts=[query_text], n_results=min(k, col.count()))
    except Exception:
        return []
    docs = (res.get("documents") or [[]])[0]
    metas = (res.get("metadatas") or [[]])[0]
    return [{"text": d, "source": m.get("source", "")}
            for d, m in zip(docs, metas)]
