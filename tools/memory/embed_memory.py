"""
Text embedding using fastembed (ONNX-based, local, no API costs)

Responsibilities:
- Generate text embeddings using BAAI/bge-small-en-v1.5 (384 dimensions)
- Convert between numpy arrays and SQLite BLOB storage
- Backfill embeddings for existing memory entries

Model downloads ~50MB on first use, cached in ~/.cache/fastembed/
"""

from typing import List
import numpy as np

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIM = 384

# Lazy-loaded model instance
_model = None


def _get_model():
    """Lazy-load fastembed model. First call downloads the model."""
    global _model
    if _model is None:
        from fastembed import TextEmbedding
        _model = TextEmbedding(model_name=EMBEDDING_MODEL)
    return _model


def embed_text(text: str) -> bytes:
    """
    Embed a single text string.

    Args:
        text: Text to embed

    Returns:
        bytes: Embedding as bytes for SQLite BLOB storage
    """
    model = _get_model()
    embeddings = list(model.embed([text]))
    vector = np.array(embeddings[0], dtype=np.float32)
    return vector.tobytes()


def embed_texts(texts: List[str]) -> List[bytes]:
    """
    Batch embed multiple texts.

    Args:
        texts: List of text strings

    Returns:
        list[bytes]: Embeddings as bytes
    """
    if not texts:
        return []
    model = _get_model()
    embeddings = list(model.embed(texts))
    return [np.array(e, dtype=np.float32).tobytes() for e in embeddings]


def bytes_to_vector(blob: bytes) -> np.ndarray:
    """Convert BLOB back to numpy array for similarity computation."""
    return np.frombuffer(blob, dtype=np.float32).copy()


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    Compute cosine similarity between two vectors.

    fastembed vectors are pre-normalized, so dot product equals cosine similarity.
    """
    return float(np.dot(a, b))


def backfill_embeddings():
    """
    One-time script to embed all existing entries without embeddings.

    Safe to run multiple times — only processes entries where embedding IS NULL.
    """
    import sys
    import os
    sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent.parent.parent))

    from tools.memory.memory_db import get_entries_without_embeddings, update_embedding

    entries = get_entries_without_embeddings(limit=1000)
    if not entries:
        print("All entries already have embeddings.")
        return

    print(f"Embedding {len(entries)} entries...")
    texts = [e['content'] for e in entries]
    blobs = embed_texts(texts)

    for entry, blob in zip(entries, blobs):
        update_embedding(entry['id'], blob, EMBEDDING_MODEL)
        print(f"  [{entry['id']}] {entry['content'][:60]}...")

    print(f"Backfilled {len(entries)} embeddings using {EMBEDDING_MODEL}.")


if __name__ == '__main__':
    backfill_embeddings()
