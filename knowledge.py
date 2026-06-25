"""
Isabella - knowledge.

Reads PDFs and text files from data/books/, chunks them, and retrieves
relevant pieces when she's forming a reply. Lightweight keyword search
that runs fine on weak hardware (no embeddings, no GPU).
"""
import os
import re
from pathlib import Path

import config

BOOKS_DIR = os.path.join(config.DATA_DIR, "books")
CHUNK_SIZE = 400  # characters per chunk
CHUNK_OVERLAP = 80

_chunks = []  # list of {"text": str, "source": str}


def _extract_pdf(path: str) -> str:
    import fitz  # PyMuPDF
    doc = fitz.open(path)
    return "\n".join(page.get_text() for page in doc)


def _extract_text(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def _split_chunks(text: str, source: str) -> list:
    chunks = []
    text = re.sub(r'\s+', ' ', text).strip()
    for i in range(0, len(text), CHUNK_SIZE - CHUNK_OVERLAP):
        chunk = text[i:i + CHUNK_SIZE]
        if len(chunk) > 50:
            chunks.append({"text": chunk, "source": source})
    return chunks


def load_books():
    """Load all PDFs and text files from data/books/ into memory."""
    global _chunks
    _chunks = []
    if not os.path.isdir(BOOKS_DIR):
        os.makedirs(BOOKS_DIR, exist_ok=True)
        return

    for file in Path(BOOKS_DIR).iterdir():
        try:
            if file.suffix.lower() == ".pdf":
                text = _extract_pdf(str(file))
            elif file.suffix.lower() in (".txt", ".md", ".csv"):
                text = _extract_text(str(file))
            else:
                continue
            _chunks.extend(_split_chunks(text, file.name))
        except Exception:
            continue

    print(f"[knowledge] loaded {len(_chunks)} chunks from {BOOKS_DIR}")


def search(query: str, top_k: int = 3) -> list:
    """Simple keyword relevance search. Returns top_k most relevant chunks."""
    if not _chunks:
        return []

    words = set(re.findall(r'\w{3,}', query.lower()))
    if not words:
        return []

    scored = []
    for chunk in _chunks:
        chunk_lower = chunk["text"].lower()
        score = sum(1 for w in words if w in chunk_lower)
        if score > 0:
            scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [c["text"] for _, c in scored[:top_k]]
