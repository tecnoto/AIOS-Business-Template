"""
Local LLM client via Ollama HTTP API

Responsibilities:
- Call local Ollama model with system prompt + user message
- Health check (is Ollama running?)
- Timeout handling (local models should respond in <30s)
- Return response text or None on failure (triggers Claude escalation)
"""

import requests
import yaml
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

_config_cache = None


def _load_config() -> dict:
    global _config_cache
    if _config_cache is not None:
        return _config_cache
    config_path = PROJECT_ROOT / 'args' / 'messaging.yaml'
    if not config_path.exists():
        return {}
    with open(config_path, 'r') as f:
        raw = yaml.safe_load(f)
    _config_cache = raw.get('messaging', {})
    return _config_cache


def is_ollama_available() -> bool:
    """Check if Ollama is running and responsive."""
    config = _load_config()
    base_url = config.get('ollama', {}).get('base_url', 'http://localhost:11434')
    try:
        resp = requests.get(f"{base_url}/api/tags", timeout=2)
        return resp.status_code == 200
    except Exception:
        return False


def call_ollama(system_prompt: str, user_message: str) -> Optional[str]:
    """
    Call local Ollama model. Returns response text or None on failure.

    On any failure (timeout, connection error, bad response), returns None
    so the caller can escalate to Claude API.
    """
    config = _load_config()
    ollama_config = config.get('ollama', {})
    base_url = ollama_config.get('base_url', 'http://localhost:11434')
    model = ollama_config.get('model', 'llama3.2:3b')
    timeout = ollama_config.get('timeout_seconds', 30)
    num_ctx = ollama_config.get('num_ctx', 8192)

    try:
        resp = requests.post(
            f"{base_url}/api/chat",
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "stream": False,
                "options": {
                    "num_ctx": num_ctx,
                    "temperature": 0.7,
                }
            },
            timeout=timeout
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get('message', {}).get('content', '').strip()
        else:
            print(f"[Ollama] API error: {resp.status_code} {resp.text[:200]}")
            return None
    except requests.Timeout:
        print(f"[Ollama] Timeout after {timeout}s")
        return None
    except requests.ConnectionError:
        print("[Ollama] Not reachable (connection refused)")
        return None
    except Exception as e:
        print(f"[Ollama] Error: {e}")
        return None
