#!/usr/bin/env python3
"""
Pre-Tool Use Hook — Deterministic Safety Guard

This hook fires BEFORE every tool execution. Claude CANNOT bypass it.
It blocks dangerous operations that should never happen automatically.

Exit codes:
  0 = Allow the tool to proceed
  2 = Block the tool with an error message (sent to stderr)
"""

import json
import sys
import re

# Read the hook input from stdin
hook_input = json.loads(sys.stdin.read())
tool_name = hook_input.get("tool_name", "")
tool_input = hook_input.get("tool_input", {})

# === BLOCKED PATTERNS ===

# 1. Destructive file operations
if tool_name == "Bash":
    command = tool_input.get("command", "")

    # Block rm -rf on anything outside .tmp/
    if re.search(r'rm\s+-rf\s+(?!.*\.tmp)', command):
        print("BLOCKED: rm -rf is only allowed on .tmp/ directories", file=sys.stderr)
        sys.exit(2)

    # Block force push to main/master
    if re.search(r'git\s+push\s+.*--force.*\b(main|master)\b', command):
        print("BLOCKED: Force push to main/master is not allowed", file=sys.stderr)
        sys.exit(2)

    if re.search(r'git\s+push\s+.*\b(main|master)\b.*--force', command):
        print("BLOCKED: Force push to main/master is not allowed", file=sys.stderr)
        sys.exit(2)

    # Block dropping databases
    if re.search(r'DROP\s+(TABLE|DATABASE)', command, re.IGNORECASE):
        print("BLOCKED: DROP TABLE/DATABASE requires manual execution", file=sys.stderr)
        sys.exit(2)

# 2. Credential file writes
if tool_name in ("Write", "Edit"):
    file_path = tool_input.get("file_path", "")
    protected_files = [".env", "credentials.json", "token.json", "setup_config.yaml"]
    for pf in protected_files:
        if file_path.endswith(pf):
            print(f"BLOCKED: Direct writes to {pf} are not allowed. Use setup.py or manual editing.", file=sys.stderr)
            sys.exit(2)

# 3. Check for API keys in commands (basic pattern)
if tool_name == "Bash":
    command = tool_input.get("command", "")
    # Detect common API key patterns being echoed or logged
    if re.search(r'(echo|printf|cat).*\b(sk-[a-zA-Z0-9]{20,}|AKIA[A-Z0-9]{16})\b', command):
        print("BLOCKED: Command appears to expose API keys", file=sys.stderr)
        sys.exit(2)

# All checks passed — allow the tool
sys.exit(0)
