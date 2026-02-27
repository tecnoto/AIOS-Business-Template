"""
SQLite CRUD operations for typed memory entries

Responsibilities:
- Schema migration (add embedding column if missing)
- Centralized read/write for memory_entries table
- Embedding storage and retrieval
- Keyword search

Usage:
    python tools/memory/memory_db.py --action search --query "keyword"
    python tools/memory/memory_db.py --action recent --limit 10
    python tools/memory/memory_db.py --action add --content "fact" --type fact --importance 7
"""

import sqlite3
import os
import sys
import argparse
import json
from datetime import datetime
from typing import Optional, List, Tuple
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATABASE_PATH = os.getenv('DATABASE_PATH', str(PROJECT_ROOT / 'data' / 'memory.db'))


def _get_connection():
    """Get database connection with WAL mode for concurrent reads."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def ensure_schema():
    """Run migrations if columns don't exist. Idempotent."""
    conn = _get_connection()
    cursor = conn.cursor()

    # Check existing columns
    cursor.execute("PRAGMA table_info(memory_entries)")
    columns = {row[1] for row in cursor.fetchall()}

    if 'embedding' not in columns:
        cursor.execute("ALTER TABLE memory_entries ADD COLUMN embedding BLOB")

    if 'embedding_model' not in columns:
        cursor.execute("ALTER TABLE memory_entries ADD COLUMN embedding_model TEXT")

    if 'updated_at' not in columns:
        cursor.execute("ALTER TABLE memory_entries ADD COLUMN updated_at DATETIME")

    if 'source' not in columns:
        cursor.execute("ALTER TABLE memory_entries ADD COLUMN source TEXT DEFAULT 'manual'")

    conn.commit()
    conn.close()


def add_entry(content: str, entry_type: str = 'fact', source: str = 'manual',
              importance: int = 5, embedding: Optional[bytes] = None,
              embedding_model: Optional[str] = None) -> int:
    """
    Insert a memory entry.

    Args:
        content: The text content
        entry_type: One of: fact, preference, event, insight, task, relationship, note, research
        source: Where it came from (manual, telegram, telegram_conversation, etc.)
        importance: 1-10 scale
        embedding: Optional pre-computed embedding as bytes
        embedding_model: Model name used for embedding

    Returns:
        int: Entry ID
    """
    ensure_schema()
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO memory_entries
        (content, entry_type, source, importance, created_at, embedding, embedding_model)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        content.strip(),
        entry_type,
        source,
        importance,
        datetime.now().isoformat(),
        embedding,
        embedding_model
    ))

    entry_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return entry_id


def get_entry(entry_id: int) -> Optional[dict]:
    """Fetch single entry by ID."""
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, content, entry_type, source, importance, created_at, updated_at
        FROM memory_entries WHERE id = ?
    ''', (entry_id,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        'id': row[0], 'content': row[1], 'entry_type': row[2],
        'source': row[3], 'importance': row[4], 'created_at': row[5],
        'updated_at': row[6]
    }


def search_keyword(query: str, limit: int = 10) -> List[dict]:
    """
    SQL LIKE keyword search.

    Args:
        query: Search string (supports multiple words, all must match)
        limit: Max results

    Returns:
        list[dict]: Matching entries sorted by importance then date
    """
    conn = _get_connection()
    cursor = conn.cursor()

    # Split query into words, each must match
    words = query.strip().split()
    if not words:
        conn.close()
        return []

    conditions = ["content LIKE ?"] * len(words)
    params = [f"%{w}%" for w in words]

    where = " AND ".join(conditions)
    params.append(limit)

    cursor.execute(f'''
        SELECT id, content, entry_type, source, importance, created_at
        FROM memory_entries
        WHERE {where}
        ORDER BY importance DESC, created_at DESC
        LIMIT ?
    ''', params)

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            'id': r[0], 'content': r[1], 'entry_type': r[2],
            'source': r[3], 'importance': r[4], 'created_at': r[5]
        }
        for r in rows
    ]


def get_entries_without_embeddings(limit: int = 100) -> List[dict]:
    """Find entries that need embedding backfill."""
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, content, entry_type, source, importance, created_at
        FROM memory_entries
        WHERE embedding IS NULL
        LIMIT ?
    ''', (limit,))

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            'id': r[0], 'content': r[1], 'entry_type': r[2],
            'source': r[3], 'importance': r[4], 'created_at': r[5]
        }
        for r in rows
    ]


def update_embedding(entry_id: int, embedding: bytes, model: str) -> bool:
    """Store embedding BLOB for an entry."""
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE memory_entries
        SET embedding = ?, embedding_model = ?, updated_at = ?
        WHERE id = ?
    ''', (embedding, model, datetime.now().isoformat(), entry_id))

    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success


def get_all_embeddings() -> List[tuple]:
    """
    Load all entries with embeddings for similarity search.

    Returns:
        list of (id, embedding_blob, content, entry_type, importance, created_at, source)
    """
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, embedding, content, entry_type, importance, created_at, source
        FROM memory_entries
        WHERE embedding IS NOT NULL
        ORDER BY created_at DESC
    ''')

    rows = cursor.fetchall()
    conn.close()
    return rows


def get_recent_entries(limit: int = 10) -> List[dict]:
    """Most recent entries, any type."""
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, content, entry_type, source, importance, created_at
        FROM memory_entries
        ORDER BY created_at DESC
        LIMIT ?
    ''', (limit,))

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            'id': r[0], 'content': r[1], 'entry_type': r[2],
            'source': r[3], 'importance': r[4], 'created_at': r[5]
        }
        for r in rows
    ]


def main():
    parser = argparse.ArgumentParser(description='Memory database operations')
    parser.add_argument('--action', required=True,
                        choices=['search', 'recent', 'add', 'migrate'],
                        help='Action to perform')
    parser.add_argument('--query', help='Search query')
    parser.add_argument('--content', help='Content for add action')
    parser.add_argument('--type', default='fact', help='Entry type')
    parser.add_argument('--importance', type=int, default=5, help='Importance 1-10')
    parser.add_argument('--source', default='manual', help='Source identifier')
    parser.add_argument('--limit', type=int, default=10, help='Result limit')
    parser.add_argument('--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()

    if args.action == 'migrate':
        ensure_schema()
        print("Schema migration complete.")

    elif args.action == 'search':
        if not args.query:
            print("Error: --query required for search")
            sys.exit(1)
        results = search_keyword(args.query, limit=args.limit)
        if args.json:
            print(json.dumps(results, indent=2))
        elif not results:
            print(f"No results for: {args.query}")
        else:
            for r in results:
                print(f"  [{r['id']}] [{r['entry_type']}] {r['content'][:80]}")
                print(f"       importance={r['importance']} source={r['source']} {r['created_at']}")

    elif args.action == 'recent':
        results = get_recent_entries(limit=args.limit)
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            for r in results:
                print(f"  [{r['id']}] [{r['entry_type']}] {r['content'][:80]}")

    elif args.action == 'add':
        if not args.content:
            print("Error: --content required for add")
            sys.exit(1)
        entry_id = add_entry(args.content, args.type, args.source, args.importance)
        print(f"Added entry {entry_id}")


if __name__ == '__main__':
    main()
