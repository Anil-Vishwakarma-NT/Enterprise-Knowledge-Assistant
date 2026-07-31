from __future__ import annotations
from typing import List, Dict, Any
import chromadb

from src.config import VECTORSTORE_DIR, CHROMA_COLLECTION_NAME

_client = None
_collection = None

def get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=VECTORSTORE_DIR)
        _collection = _client.get_or_create_collection(
            name=CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection

def upsert_chunks(ids, embeddings, documents, metadatas) -> None:
    get_collection().upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)

def query(embedding: List[float], top_k: int) -> Dict[str, Any]:
    return get_collection().query(query_embeddings=[embedding], n_results=top_k)

def delete_by_source(source: str) -> None:
    """Wipe old chunks for a file before re-indexing it (handles edits)."""
    get_collection().delete(where={"source": source})