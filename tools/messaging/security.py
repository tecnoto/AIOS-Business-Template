"""
Security middleware for the messaging layer

Responsibilities:
- Rate limiting via in-memory sliding window
- Blocked pattern detection (regex-based)
- Confirmation gate for destructive operations
- Config loaded from args/messaging.yaml

Usage (imported by telegram_handler.py):
    from tools.messaging.security import check_rate_limit, check_blocked_patterns, needs_confirmation
"""

import re
import time
import yaml
from collections import defaultdict
from pathlib import Path
from typing import Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = PROJECT_ROOT / 'args' / 'messaging.yaml'

# In-memory rate limit storage: {user_id: [timestamp, timestamp, ...]}
_rate_limit_windows = defaultdict(list)

# Cached config
_config = None


def _load_config() -> dict:
    """Load and cache messaging config from args/messaging.yaml."""
    global _config
    if _config is not None:
        return _config

    if not CONFIG_PATH.exists():
        _config = {}
        return _config

    with open(CONFIG_PATH, 'r') as f:
        raw = yaml.safe_load(f)

    _config = raw.get('messaging', {})
    return _config


def reload_config():
    """Force reload config (useful after config changes)."""
    global _config
    _config = None
    return _load_config()


def get_allowed_users() -> list:
    """Return list of allowed user IDs as strings."""
    config = _load_config()
    return config.get('security', {}).get('allowed_users', [])


def is_user_allowed(user_id) -> bool:
    """Check if a user ID is in the whitelist.

    Args:
        user_id: Telegram user ID (int or str)

    Returns:
        bool: True if allowed, False if blocked
    """
    allowed = get_allowed_users()
    if not allowed:
        # No whitelist configured — allow all (open mode)
        return True
    return str(user_id) in [str(u) for u in allowed]


def check_rate_limit(user_id) -> Tuple[bool, Optional[str]]:
    """Check if user has exceeded the rate limit.

    Uses a sliding window: counts messages in the last 60 seconds.

    Args:
        user_id: Telegram user ID (int or str)

    Returns:
        (allowed, message): allowed=True if under limit, message=cooldown text if blocked
    """
    config = _load_config()
    rate_config = config.get('security', {}).get('rate_limit', {})
    max_per_minute = rate_config.get('max_messages_per_minute', 30)
    cooldown_msg = rate_config.get('cooldown_message', 'Rate limit reached. Wait a moment.')

    user_key = str(user_id)
    now = time.time()
    window_start = now - 60.0

    # Prune timestamps older than 60 seconds
    _rate_limit_windows[user_key] = [
        ts for ts in _rate_limit_windows[user_key]
        if ts > window_start
    ]

    if len(_rate_limit_windows[user_key]) >= max_per_minute:
        return False, cooldown_msg

    # Record this request
    _rate_limit_windows[user_key].append(now)
    return True, None


def check_blocked_patterns(message: str) -> Tuple[bool, Optional[str]]:
    """Check message against blocked regex patterns.

    Args:
        message: The user's message text

    Returns:
        (safe, matched_pattern): safe=True if no blocked patterns found,
        matched_pattern is the pattern that matched if blocked
    """
    config = _load_config()
    patterns = config.get('security', {}).get('blocked_patterns', [])

    for pattern in patterns:
        try:
            if re.search(pattern, message, re.IGNORECASE):
                return False, pattern
        except re.error:
            # Skip invalid regex patterns
            continue

    return True, None


def needs_confirmation(message: str) -> bool:
    """Check if message contains destructive keywords requiring confirmation.

    Args:
        message: The user's message text

    Returns:
        bool: True if confirmation should be requested
    """
    config = _load_config()
    keywords = config.get('security', {}).get('confirmation_required', [])

    message_lower = message.lower()
    for keyword in keywords:
        if keyword.lower() in message_lower:
            return True

    return False


def run_all_checks(user_id, message: str) -> Tuple[bool, Optional[str]]:
    """Run all security checks in order.

    Order: whitelist → rate limit → blocked patterns.
    Confirmation check is NOT included here (handled separately by the handler).

    Args:
        user_id: Telegram user ID
        message: The user's message text

    Returns:
        (passed, reason): passed=True if all checks pass, reason explains rejection
    """
    # 1. Whitelist check
    if not is_user_allowed(user_id):
        return False, "unauthorized"

    # 2. Rate limit
    allowed, cooldown_msg = check_rate_limit(user_id)
    if not allowed:
        return False, cooldown_msg

    # 3. Blocked patterns
    safe, matched = check_blocked_patterns(message)
    if not safe:
        return False, "blocked"

    return True, None
