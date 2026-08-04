from __future__ import annotations
import hashlib, json, os
from typing import Dict

from src.config import DATA_DIR, INGESTION_MANIFEST_PATH
from src.ingestion.loader import list_supported_files, load_file
from src.ingestion.chunker import chunk_pages
from src.rag.embedder import embed_texts
from src.rag.vectorstore import upsert_chunks, delete_by_source

def _file_hash(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(8192), b""):
            h.update(block)
    return h.hexdigest()

def _load_manifest() -> Dict[str, str]:
    if os.path.exists(INGESTION_MANIFEST_PATH):
        with open(INGESTION_MANIFEST_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def _save_manifest(manifest: Dict[str, str]) -> None:
    with open(INGESTION_MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

def ingest_file(path: str) -> int:
    source_name = os.path.basename(path)
    delete_by_source(source_name)
    pages = load_file(path)
    chunks = chunk_pages(pages)
    if not chunks:
        return 0
    texts = [c.text for c in chunks]
    embeddings = embed_texts(texts)
    ids = [c.id for c in chunks]
    metadatas = [{"source": c.source, "page": c.page} for c in chunks]
    upsert_chunks(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
    return len(chunks)

def run_incremental_ingestion(verbose: bool = True) -> Dict[str, int]:
    manifest = _load_manifest()
    results: Dict[str, int] = {}

    files = list_supported_files(DATA_DIR)
    current_names = {os.path.basename(p) for p in files}

    # Drop entries for files removed from data/
    for stale_name in list(manifest.keys()):
        if stale_name not in current_names:
            delete_by_source(stale_name)
            manifest.pop(stale_name, None)

    for path in files:
        name = os.path.basename(path)
        current_hash = _file_hash(path)
        if manifest.get(name) == current_hash:
            continue  # unchanged, skip
        n_chunks = ingest_file(path)
        manifest[name] = current_hash
        results[name] = n_chunks
        if verbose:
            print(f"[ingestion] indexed '{name}' -> {n_chunks} chunks")

    _save_manifest(manifest)
    return results

if __name__ == "__main__":
    run_incremental_ingestion()