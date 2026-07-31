from __future__ import annotations
from dataclasses import dataclass
from typing import List

from src.config import CHUNK_SIZE, CHUNK_OVERLAP
from src.ingestion.loader import RawPage

@dataclass
class Chunk:
    id: str
    text: str
    source: str
    page: int

def _split_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    text = " ".join(text.split())
    if len(text) <= chunk_size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start = end - overlap
    return chunks

def chunk_pages(pages: List[RawPage]) -> List[Chunk]:
    chunks: List[Chunk] = []
    for page in pages:
        pieces = _split_text(page.text, CHUNK_SIZE, CHUNK_OVERLAP)
        for i, piece in enumerate(pieces):
            chunk_id = f"{page.source}::p{page.page}::c{i}"
            chunks.append(Chunk(id=chunk_id, text=piece, source=page.source, page=page.page))
    return chunks