from __future__ import annotations
from typing import List
import litellm

from src.config import OLLAMA_EMBED_MODEL, OLLAMA_API_BASE

_LITELLM_EMBED_MODEL = f"ollama/{OLLAMA_EMBED_MODEL}"

def embed_texts(texts: List[str]) -> List[List[float]]:
    if not texts:
        return []
    response = litellm.embedding(
        model=_LITELLM_EMBED_MODEL,
        input=texts,
        api_base=OLLAMA_API_BASE,
    )
    return [item["embedding"] for item in response["data"]]

def embed_query(query: str) -> List[float]:
    return embed_texts([query])[0]