from typing import List, Dict, Any, Optional
from embeddings.faiss_store import search
from config import TOP_K


def retrieve(
    query: str,
    patient_id: Optional[str] = None,
    top_k: int = TOP_K,
) -> List[Dict[str, Any]]:
    """
    Run semantic search and return top_k relevant chunks.
    When patient_id is provided, results are scoped to that patient only.
    """
    results = search(query, top_k=top_k, patient_id=patient_id)
    return results


def build_context(chunks: List[Dict[str, Any]]) -> str:
    """
    Concatenate retrieved chunks into a single context string for the LLM prompt.
    Each chunk is separated with a divider and labelled by source type.
    """
    if not chunks:
        return "No relevant medical records found."

    parts = []
    for i, chunk in enumerate(chunks, 1):
        source = chunk.get("source_type", "record").title()
        parts.append(
            f"[Context {i} — {source}]\n{chunk['text'].strip()}"
        )
    return "\n\n---\n\n".join(parts)
