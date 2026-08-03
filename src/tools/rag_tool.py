"""
FR-3: RAG Search - exposes the vector retriever as an agent tool.
"""
from src.rag.retriever import retrieve

def search_documents(query: str) -> dict:
    """Search the enterprise document knowledge base for relevant passages."""
    hits = retrieve(query, top_k=4)
    if not hits:
        return {"results": [], "message": "No indexed documents matched this query."}
    return {"results": hits}