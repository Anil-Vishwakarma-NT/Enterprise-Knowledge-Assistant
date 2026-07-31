from __future__ import annotations
from typing import List, Dict, Any

from src.ingestion.run_ingestion import run_incremental_ingestion
from src.rag.embedder import embed_query
from src.rag.vectorstore import query as vector_query
from src.config import TOP_K_DEFAULT

def retrieve(query_text: str, top_k: int = TOP_K_DEFAULT) -> List[Dict[str, Any]]:
    run_incremental_ingestion(verbose=False)  # picks up newly uploaded docs

    query_embedding = embed_query(query_text)
    results = vector_query(query_embedding, top_k=top_k)

    hits: List[Dict[str, Any]] = []
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for text, meta, distance in zip(documents, metadatas, distances):
        hits.append({
            "text": text,
            "source": meta.get("source"),
            "page": meta.get("page"),
            "score": round(1 - distance, 4),
        })
    return hits