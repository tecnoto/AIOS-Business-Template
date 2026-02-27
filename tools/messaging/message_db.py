"""
Full conversation history database

Responsibilities:
- Store every message with timestamps, direction, platform
- Retrieve recent conversation for context injection
- Format conversation transcript for Claude prompts
- Persists across bot restarts (replaces in-memory deque)
"""

import sqlite3
import os
import json
from datetime import datetime
from typing import Optional, List
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ACTIVITY_DB = os.getenv('ACTIVITY_DB_PATH', str(PROJECT_ROOT / 'data' / 'activity.db'))


def _get_connection():
    """Get database connection with WAL mode."""
    conn = sqlite3.connect(ACTIVITY_DB)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def ensure_schema():
    """Create messages table if it doesn't exist. Idempotent."""
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            platform TEXT DEFAULT 'telegram',
            direction TEXT NOT NULL,
            content TEXT NOT NULL,
            intent TEXT,
            metadata TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create index for fast retrieval by user + time
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_messages_user_time
        ON messages(user_id, created_at DESC)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_messages_platform
        ON messages(platform)
    ''')

    conn.commit()
    conn.close()


def save_message(user_id: str, direction: str, content: str,
                 platform: str = 'telegram', intent: Optional[str] = None,
                 metadata: Optional[dict] = None) -> int:
    """
    Save a message to the conversation history.

    Args:
        user_id: User identifier
        direction: 'inbound' (user) or 'outbound' (bot)
        content: Message text
        platform: Platform identifier (telegram, cli, etc.)
        intent: Optional classified intent
        metadata: Optional JSON-serializable extra data

    Returns:
        int: Message ID
    """
    ensure_schema()
    conn = _get_connection()
    cursor = conn.cursor()

    metadata_json = json.dumps(metadata) if metadata else None

    cursor.execute('''
        INSERT INTO messages (user_id, platform, direction, content, intent, metadata, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        str(user_id),
        platform,
        direction,
        content,
        intent,
        metadata_json,
        datetime.now().isoformat()
    ))

    msg_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return msg_id


def get_recent_messages(user_id: str, limit: int = 20,
                        platform: Optional[str] = 'telegram') -> List[dict]:
    """
    Get last N messages for a user, ordered chronologically (oldest first).

    Args:
        user_id: User identifier
        limit: Max messages to return
        platform: Filter by platform (None for all)

    Returns:
        list[dict]: Messages in chronological order
    """
    ensure_schema()
    conn = _get_connection()
    cursor = conn.cursor()

    if platform:
        cursor.execute('''
            SELECT id, user_id, platform, direction, content, intent, metadata, created_at
            FROM messages
            WHERE user_id = ? AND platform = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (str(user_id), platform, limit))
    else:
        cursor.execute('''
            SELECT id, user_id, platform, direction, content, intent, metadata, created_at
            FROM messages
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (str(user_id), limit))

    rows = cursor.fetchall()
    conn.close()

    # Reverse to chronological order (oldest first)
    rows.reverse()

    return [
        {
            'id': r[0],
            'user_id': r[1],
            'platform': r[2],
            'direction': r[3],
            'content': r[4],
            'intent': r[5],
            'metadata': json.loads(r[6]) if r[6] else None,
            'created_at': r[7],
        }
        for r in rows
    ]


def format_conversation_for_prompt(user_id: str, limit: int = 20,
                                    platform: str = 'telegram') -> str:
    """
    Format recent messages as a conversation transcript for Claude.

    Args:
        user_id: User identifier
        limit: Max messages to include
        platform: Platform filter

    Returns:
        str: Formatted conversation (empty string if no history)
    """
    messages = get_recent_messages(user_id, limit=limit, platform=platform)

    if not messages:
        return ""

    lines = []
    for msg in messages:
        role = "User" if msg['direction'] == 'inbound' else "Assistant"
        # Truncate very long messages in context
        content = msg['content']
        if len(content) > 500:
            content = content[:500] + "..."
        lines.append(f"{role}: {content}")

    return "\n".join(lines)


def get_message_count(user_id: str, platform: str = 'telegram') -> int:
    """Get total message count for a user."""
    ensure_schema()
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT COUNT(*) FROM messages
        WHERE user_id = ? AND platform = ?
    ''', (str(user_id), platform))

    count = cursor.fetchone()[0]
    conn.close()
    return count
