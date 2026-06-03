from typing import List, Dict, Any
from config import CHUNK_SIZE, CHUNK_OVERLAP


def chunk_text(text: str) -> List[str]:
    """
    Split a text string into overlapping chunks of CHUNK_SIZE characters.
    Overlap helps preserve context across chunk boundaries.
    """
    if len(text) <= CHUNK_SIZE:
        return [text]

    chunks = []
    start  = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append(text[start:end])
        start += CHUNK_SIZE - CHUNK_OVERLAP  # slide window with overlap
    return chunks


def chunk_documents(docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Take a list of document dicts and split their text into chunks.
    Preserves all metadata fields (patient_id, source_type, source_id).
    Returns flat list of chunk dicts with an additional 'chunk_index'.
    """
    chunked = []
    for doc in docs:
        text_chunks = chunk_text(doc["text"])
        for idx, chunk in enumerate(text_chunks):
            chunked.append({
                **doc,
                "text":        chunk,
                "chunk_index": idx,
            })
    return chunked
