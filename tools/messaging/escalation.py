"""
Escalation logic: decides whether to use local LLM or Claude API

Responsibilities:
- Keyword-based fast-path escalation (deterministic, instant)
- Message length check
- Explicit user escalation triggers (@claude, /claude)
- Self-assessment marker detection (post-response from local LLM)
- Workflow trigger detection (reuses workflow_registry)
"""

import sys
import yaml
from pathlib import Path
from typing import Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

_config = None


def _load_config() -> dict:
    global _config
    if _config is not None:
        return _config
    config_path = PROJECT_ROOT / 'args' / 'messaging.yaml'
    if not config_path.exists():
        return {}
    with open(config_path, 'r') as f:
        raw = yaml.safe_load(f)
    _config = raw.get('messaging', {}).get('escalation', {})
    return _config


def should_escalate(message: str) -> Tuple[bool, str]:
    """
    Determine if a message should bypass local LLM and go directly to Claude.

    Returns:
        (escalate: bool, reason: str)
    """
    config = _load_config()
    msg_lower = message.lower().strip()

    # 1. Explicit escalation triggers (@claude, /claude)
    explicit = config.get('explicit_escalation_triggers', ['@claude', '/claude'])
    for trigger in explicit:
        if trigger.lower() in msg_lower:
            return True, f"explicit_trigger:{trigger}"

    # 2. Workflow keywords (reuse existing registry)
    try:
        from tools.telegram.workflow_registry import detect_workflow
        wf = detect_workflow(message)
        if wf.get('detected'):
            return True, f"workflow_detected:{wf['goal']}"
    except ImportError:
        pass

    # 3. Keyword-based escalation
    keywords = config.get('always_escalate_keywords', [])
    for keyword in keywords:
        if keyword.lower() in msg_lower:
            return True, f"keyword:{keyword}"

    # 4. Message length check (complex requests tend to be longer)
    max_len = config.get('max_local_message_length', 500)
    if len(message) > max_len:
        return True, f"message_length:{len(message)}"

    return False, "local"


def response_requests_escalation(response_text: str) -> bool:
    """Check if the local LLM's response contains a self-escalation marker."""
    config = _load_config()
    marker = config.get('self_assessment_marker', '[ESCALATE]')
    return marker in response_text
