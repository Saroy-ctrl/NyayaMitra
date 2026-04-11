"""
chroma_service.py -- ChromaDB singleton and query interface for NyayaMitra.

Provides lazy-initialized access to the indian_laws collection.
query_laws() performs semantic search over indexed legal sections.
"""

from __future__ import annotations

import logging
from pathlib import Path

import chromadb

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level singletons (lazy-initialized)
# ---------------------------------------------------------------------------
_client: chromadb.PersistentClient | None = None
_collection = None

COLLECTION_NAME = "indian_laws"


def init_chroma() -> chromadb.PersistentClient:
    """
    Initialize the ChromaDB persistent client.

    The database is stored at backend/chroma_db/ (resolved relative to this
    file's location so it works regardless of the caller's cwd).
    Sets the module-level _client global and returns the client.
    """
    global _client
    db_path = Path(__file__).parent.parent / "chroma_db"
    _client = chromadb.PersistentClient(path=str(db_path))
    return _client


def get_collection():
    """
    Return the indian_laws ChromaDB collection, initializing lazily on first call.

    Uses cosine distance for semantic similarity matching.
    Caches the collection in the module-level _collection global.
    """
    global _client, _collection

    if _collection is None:
        if _client is None:
            init_chroma()
        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    return _collection


def get_indexed_count() -> int:
    """Return the total number of law sections currently stored in ChromaDB."""
    try:
        return get_collection().count()
    except Exception:
        return 0


async def query_laws(
    incident_type: str,
    description: str,
    top_k: int = 8,
    where: dict | None = None,
) -> list[dict]:
    """
    Perform semantic search over the indexed Indian legal corpus.

    Builds a combined query string from the incident type and description,
    then retrieves the top_k most relevant law sections by cosine similarity.

    Args:
        incident_type: Category of the legal matter (e.g. "cheque bounce", "theft").
        description:   Free-text description of the user's situation.
        top_k:         Maximum number of results to return (default 8).
        where:         Optional ChromaDB metadata filter dict, e.g. {"act": "Bharatiya Nyaya Sanhita 2023"}.

    Returns:
        List of dicts, each with keys:
            section_number  -- e.g. "138"
            act             -- e.g. "Negotiable Instruments Act 1881"
            title           -- e.g. "Dishonour of cheque for insufficiency of funds"
            text            -- Full statutory text (embedding document)
            relevance_score -- Float in [0, 1]; higher = more relevant
        Returns an empty list if the collection is empty or on any error.
    """
    try:
        count = get_indexed_count()
        if count == 0:
            logger.warning("ChromaDB collection is empty -- run seed_chroma.py first")
            return []

        query_string = f"{incident_type} {description}"
        n_results = min(top_k, count)

        query_kwargs: dict = {
            "query_texts": [query_string],
            "n_results": n_results,
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            query_kwargs["where"] = where

        results = get_collection().query(**query_kwargs)

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        law_sections: list[dict] = []
        for doc, meta, dist in zip(documents, metadatas, distances):
            law_sections.append(
                {
                    "section_number": meta.get("section", ""),
                    "act": meta.get("act", ""),
                    "title": meta.get("title", ""),
                    "text": doc,
                    "relevance_score": round(1.0 - dist, 4),
                }
            )

        return law_sections

    except Exception as exc:
        logger.warning("query_laws failed: %s", exc)
        return []
