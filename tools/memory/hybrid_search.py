"""
Hybrid search combining keyword and semantic search

Responsibilities:
- Run both keyword search (SQL LIKE) and semantic search (vector similarity)
- Merge results using Reciprocal Rank Fusion (RRF)
- Return best combined results

Usage:
    python tools/memory/hybrid_search.py --query "what does user prefer"
"""

import sys
import argparse
import json
from typing import List
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def hybrid_search(query: str, top_k: int = 5,
                  keyword_weight: float = 0.3,
                  semantic_weight: float = 0.7) -> List[dict]:
    """
    Combined keyword + semantic search using Reciprocal Rank Fusion.

    Args:
        query: Natural language search query
        top_k: Number of results to return
        keyword_weight: Weight for keyword search results (0.0 - 1.0)
        semantic_weight: Weight for semantic search results (0.0 - 1.0)

    Returns:
        list[dict]: Merged results with 'rrf_score' field
    """
    from tools.memory.memory_db import search_keyword
    from tools.memory.semantic_search import semantic_search

    # Run both searches with expanded result sets
    keyword_results = search_keyword(query, limit=top_k * 3)
    semantic_results = semantic_search(query, top_k=top_k * 3, min_score=0.2)

    # Reciprocal Rank Fusion
    k = 60  # RRF constant (standard value)
    scores = {}   # entry_id -> fused score
    entries = {}  # entry_id -> entry dict

    for rank, entry in enumerate(keyword_results):
        eid = entry['id']
        scores[eid] = scores.get(eid, 0) + keyword_weight * (1.0 / (k + rank + 1))
        entries[eid] = entry

    for rank, entry in enumerate(semantic_results):
        eid = entry['id']
        scores[eid] = scores.get(eid, 0) + semantic_weight * (1.0 / (k + rank + 1))
        if eid not in entries:
            entries[eid] = entry
        # Preserve semantic score for display
        entries[eid]['semantic_score'] = entry.get('score', 0)

    # Sort by fused score
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    results = []
    for eid, rrf_score in ranked[:top_k]:
        entry = entries[eid]
        entry['rrf_score'] = round(rrf_score, 6)
        results.append(entry)

    return results


def main():
    parser = argparse.ArgumentParser(description='Hybrid keyword + semantic search')
    parser.add_argument('--query', required=True, help='Search query')
    parser.add_argument('--top-k', type=int, default=5, help='Number of results')
    parser.add_argument('--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()
    results = hybrid_search(args.query, top_k=args.top_k)

    if args.json:
        print(json.dumps(results, indent=2))
    elif not results:
        print(f"No results for: {args.query}")
    else:
        print(f"Hybrid search results for '{args.query}' ({len(results)}):\n")
        for r in results:
            sem = r.get('semantic_score', '-')
            print(f"  [{r['id']}] (rrf={r['rrf_score']}, sem={sem}) [{r.get('entry_type', '?')}]")
            print(f"       {r['content'][:100]}")
            print()


if __name__ == '__main__':
    main()
