"""
Semantic search over memory entries using vector similarity

Responsibilities:
- Embed query text
- Compare against all stored embeddings
- Return results ranked by cosine similarity

Usage:
    python tools/memory/semantic_search.py --query "related concept"
"""

import sys
import argparse
import json
from typing import List
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np


def semantic_search(query: str, top_k: int = 5, min_score: float = 0.3) -> List[dict]:
    """
    Search memory by semantic similarity.

    Args:
        query: Natural language query
        top_k: Number of results to return
        min_score: Minimum cosine similarity threshold (0.0 - 1.0)

    Returns:
        list[dict]: Entries with 'score' field, sorted by relevance
    """
    from tools.memory.embed_memory import embed_text, bytes_to_vector
    from tools.memory.memory_db import get_all_embeddings

    # Embed the query
    query_blob = embed_text(query)
    query_vec = bytes_to_vector(query_blob)

    # Load all stored embeddings
    entries = get_all_embeddings()
    if not entries:
        return []

    # Compute similarities
    results = []
    for entry_id, emb_blob, content, entry_type, importance, created_at, source in entries:
        if emb_blob is None:
            continue
        entry_vec = bytes_to_vector(emb_blob)
        score = float(np.dot(query_vec, entry_vec))
        if score >= min_score:
            results.append({
                'id': entry_id,
                'content': content,
                'entry_type': entry_type,
                'importance': importance,
                'source': source,
                'created_at': created_at,
                'score': round(score, 4),
            })

    # Sort by score descending
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:top_k]


def main():
    parser = argparse.ArgumentParser(description='Semantic search over memory')
    parser.add_argument('--query', required=True, help='Search query')
    parser.add_argument('--top-k', type=int, default=5, help='Number of results')
    parser.add_argument('--min-score', type=float, default=0.3, help='Minimum similarity')
    parser.add_argument('--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()
    results = semantic_search(args.query, top_k=args.top_k, min_score=args.min_score)

    if args.json:
        print(json.dumps(results, indent=2))
    elif not results:
        print(f"No semantically similar results for: {args.query}")
    else:
        print(f"Semantic search results for '{args.query}' ({len(results)}):\n")
        for r in results:
            print(f"  [{r['id']}] (score={r['score']}) [{r['entry_type']}]")
            print(f"       {r['content'][:100]}")
            print()


if __name__ == '__main__':
    main()
