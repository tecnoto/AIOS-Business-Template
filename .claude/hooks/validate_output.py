#!/usr/bin/env python3
"""
Post-Tool Use Hook — Output Validation

Runs AFTER Bash tool execution. Validates script output and flags failures.
Non-blocking: warns Claude but never prevents tool completion.

Exit code 0 = validation passed (or not applicable)
Prints warnings so Claude can react to them.
"""

import json
import re
import sys

# Patterns that indicate secrets leaked in output
SECRET_PATTERNS = [
    r"sk-[A-Za-z0-9_-]{20,}",
    r"pk_(?:live|test)_[A-Za-z0-9]{20,}",
    r"xoxb-[A-Za-z0-9-]{20,}",
    r"ghp_[A-Za-z0-9]{20,}",
    r"pcsk_[A-Za-z0-9_-]{20,}",
    r"AKIA[A-Z0-9]{16}",
    r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}",
]


def check_for_secrets(output: str) -> list:
    """Scan output for leaked credentials."""
    found = []
    for pattern in SECRET_PATTERNS:
        if re.search(pattern, output):
            found.append(pattern.split("[")[0].rstrip("\\"))
    return found


def validate_json_output(output: str) -> dict:
    """Check if script output is valid JSON with expected structure."""
    try:
        data = json.loads(output)
    except json.JSONDecodeError as e:
        return {"valid": False, "reason": f"Script output is not valid JSON: {e}"}

    if isinstance(data, dict) and data.get("success") is False:
        error = data.get("error", "Unknown error")
        return {"valid": False, "reason": f"Script reported failure: {error}"}

    return {"valid": True, "reason": ""}


def main():
    try:
        raw = sys.stdin.read()
        if not raw:
            sys.exit(0)

        data = json.loads(raw)
        tool_output = data.get("tool_output", "")

        if not tool_output or not tool_output.strip():
            sys.exit(0)

        stripped = tool_output.strip()

        # Check for leaked secrets in output
        leaked = check_for_secrets(stripped)
        if leaked:
            print(
                f"WARNING: Tool output may contain credentials "
                f"(matched patterns: {', '.join(leaked)}). "
                f"Do NOT send this output to external services or users."
            )

        # Validate JSON output from scripts
        if stripped.startswith("{") or stripped.startswith("["):
            result = validate_json_output(stripped)
            if not result["valid"]:
                print(f"Output validation warning: {result['reason']}")

        # Always exit 0 — PostToolUse should warn, not block
        sys.exit(0)

    except Exception:
        sys.exit(0)  # Never block on validation errors


if __name__ == "__main__":
    main()
