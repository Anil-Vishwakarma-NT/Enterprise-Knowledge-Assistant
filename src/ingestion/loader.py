from __future__ import annotations
import os
from dataclasses import dataclass
from typing import List

from pypdf import PdfReader
from docx import Document as DocxDocument

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}

@dataclass
class RawPage:
    source: str
    page: int
    text: str

def _load_pdf(path: str) -> List[RawPage]:
    reader = PdfReader(path)
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            pages.append(RawPage(source=os.path.basename(path), page=i, text=text))
    return pages

def _load_docx(path: str) -> List[RawPage]:
    doc = DocxDocument(path)
    full_text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    if not full_text.strip():
        return []
    return [RawPage(source=os.path.basename(path), page=1, text=full_text)]

def _load_text(path: str) -> List[RawPage]:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    if not text.strip():
        return []
    return [RawPage(source=os.path.basename(path), page=1, text=text)]

def load_file(path: str) -> List[RawPage]:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        return _load_pdf(path)
    if ext == ".docx":
        return _load_docx(path)
    if ext in (".txt", ".md"):
        return _load_text(path)
    raise ValueError(f"Unsupported file type: {ext}")

def list_supported_files(data_dir: str) -> List[str]:
    files = []
    for name in sorted(os.listdir(data_dir)):
        path = os.path.join(data_dir, name)
        if os.path.isfile(path) and os.path.splitext(name)[1].lower() in SUPPORTED_EXTENSIONS:
            files.append(path)
    return files