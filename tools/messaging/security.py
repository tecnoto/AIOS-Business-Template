"""
Security middleware for the messaging layer

Responsibilities:
- User whitelist (CLOSED by default — reject if no whitelist configured)
- Rate limiting via sliding window (per-minute + per-hour)
- Blocked pattern detection (regex-based)
- Confirmation gate for destructive operations
- Security event audit logging
- Config loaded from args/messaging.yaml

Usage (imported by telegram_handler.py):
    from tools.messaging.security import run_all_checks, needs_confirmation
"""

import json
import re
import time
import yaml
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = PROJECT_ROOT / 'args' / 'messaging.yaml'
SECURITY_LOG = PROJECT_ROOT / 'data' / 'security.log'

# In-memory rate limit storage: {user_id: [timestamp, ...]}
_rate_limit_windows = defaultdict(list)

# Cached config
_config = None

# Built-in blocked patterns (always active, even if config is empty)
_BUILTIN_BLOCKED = [
    r"rm\s+-rf",
    r"sudo\s+",
    r"DROP\s+TABLE",
    r"DELETE\s+FROM",
    r"chmod\s+777",
    r"eval\(",
    r"exec\(",
    r"os\.system",
    r"__import__",
    r"\|\s*sh",
    r"\|\s*bash",
    r"curl.*\|.*sh",
]


# ---------------------------------------------------------------------------
# Audit logging
# ---------------------------------------------------------------------------

def _log_security_event(event_type: str, user_id: str, detail: str):
    """Append a security event to the audit log."""
    try:
        SECURITY_LOG.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = json.dumps({
            "timestamp": timestamp,
            "event": event_type,
            "user_id": str(user_id),
            "detail": detail,
        })
        with open(SECURITY_LOG, "a") as f:
            f.write(entry + "\n")
    except Exception:
        pass  # Audit logging should never break the main flow


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Whitelist — CLOSED by default
# ---------------------------------------------------------------------------

def get_allowed_users() -> list:
    """Return list of allowed user IDs as strings."""
    config = _load_config()
    return config.get('security', {}).get('allowed_users', [])


def is_user_allowed(user_id) -> bool:
    """Check if a user ID is in the whitelist.

    CLOSED by default: if no whitelist is configured, ALL users are REJECTED.
    This prevents accidental open access when deploying without configuration.
    """
    allowed = get_allowed_users()
    if not allowed:
        _log_security_event("unauthorized", str(user_id), "No whitelist configured — all users rejected")
        return False
    if str(user_id) not in [str(u) for u in allowed]:
        _log_security_event("unauthorized", str(user_id), "User not in whitelist")
        return False
    return True


# ---------------------------------------------------------------------------
# Rate limiting (per-minute + per-hour)
# ---------------------------------------------------------------------------

def check_rate_limit(user_id) -> Tuple[bool, Optional[str]]:
    """Check if user has exceeded rate limits (per-minute and per-hour)."""
    config = _load_config()
    rate_config = config.get('security', {}).get('rate_limit', {})
    max_per_minute = rate_config.get('max_messages_per_minute', 30)
    max_per_hour = rate_config.get('max_messages_per_hour', 200)
    cooldown_msg = rate_config.get('cooldown_message', 'Rate limit reached. Wait a moment.')

    user_key = str(user_id)
    now = time.time()

    # Prune timestamps older than 1 hour
    _rate_limit_windows[user_key] = [
        ts for ts in _rate_limit_windows[user_key]
        if ts > now - 3600.0
    ]

    # Check per-minute
    recent_minute = [ts for ts in _rate_limit_windows[user_key] if ts > now - 60.0]
    if len(recent_minute) >= max_per_minute:
        _log_security_event("rate_limited", user_key, f"Exceeded {max_per_minute}/min")
        return False, cooldown_msg

    # Check per-hour
    if len(_rate_limit_windows[user_key]) >= max_per_hour:
        _log_security_event("rate_limited", user_key, f"Exceeded {max_per_hour}/hour")
        return False, cooldown_msg

    # Record this request
    _rate_limit_windows[user_key].append(now)
    return True, None


# ---------------------------------------------------------------------------
# Blocked patterns
# ---------------------------------------------------------------------------

def check_blocked_patterns(message: str) -> Tuple[bool, Optional[str]]:
    """Check message against blocked regex patterns (built-in + config)."""
    config = _load_config()
    config_patterns = config.get('security', {}).get('blocked_patterns', [])

    # Combine built-in + config patterns
    all_patterns = _BUILTIN_BLOCKED + config_patterns

    for pattern in all_patterns:
        try:
            if re.search(pattern, message, re.IGNORECASE):
                _log_security_event("blocked_pattern", "system", f"Pattern matched: {pattern}")
                return False, pattern
        except re.error:
            continue

    return True, None


# ---------------------------------------------------------------------------
# Confirmation gate
# ---------------------------------------------------------------------------

def needs_confirmation(message: str) -> bool:
    """Check if message contains destructive keywords requiring confirmation."""
    config = _load_config()
    keywords = config.get('security', {}).get('confirmation_required', [])

    message_lower = message.lower()
    for keyword in keywords:
        if keyword.lower() in message_lower:
            return True

    return False


# ---------------------------------------------------------------------------
# Composite check
# ---------------------------------------------------------------------------

def run_all_checks(user_id, message: str) -> Tuple[bool, Optional[str]]:
    """Run all security checks in order.

    Order: whitelist -> rate limit -> blocked patterns.
    Confirmation check is NOT included (handled separately by the handler).

    Returns:
        (passed, reason): passed=True if all checks pass
    """
    if not is_user_allowed(user_id):
        return False, "unauthorized"

    allowed, cooldown_msg = check_rate_limit(user_id)
    if not allowed:
        return False, cooldown_msg

    safe, matched = check_blocked_patterns(message)
    if not safe:
        return False, "blocked"

    return True, None
