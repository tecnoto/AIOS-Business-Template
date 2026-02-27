#!/usr/bin/env python3
"""
Pre-Tool Use Hook — Deterministic Safety Guard

This hook fires BEFORE every tool execution. Claude CANNOT bypass it.
It blocks dangerous operations that should never happen automatically.

Exit codes:
  0 = Allow the tool to proceed
  2 = Block the tool with an error message

Three-tier classification:
  BLOCKED  — Hard stop, exit code 2 (dangerous patterns)
  PROTECTED — Context-aware blocking (critical files)
  CAUTION  — Informational warning, still allowed (external actions)
"""

import json
import sys
import re


# ---------------------------------------------------------------------------
# Blocked command patterns — always blocked, no exceptions
# ---------------------------------------------------------------------------

BLOCKED_COMMANDS = [
    # Destructive file operations (multiple syntaxes)
    r"rm\s+(-[a-zA-Z]*r[a-zA-Z]*\s+-[a-zA-Z]*f|"
    r"-[a-zA-Z]*f[a-zA-Z]*\s+-[a-zA-Z]*r|"
    r"-rf|-fr|--recursive\s+--force|--force\s+--recursive)\s+(?!/.*\.tmp)",
    r"find\s+.*-delete",
    r"find\s+.*-exec\s+rm",
    # Git destructive operations
    r"git\s+push\s+.*(-f|--force)",
    r"git\s+reset\s+--hard",
    r"git\s+clean\s+-[a-zA-Z]*f",
    r"git\s+checkout\s+--\s+\.",
    # Database destruction
    r"DROP\s+(TABLE|DATABASE)",
    r"DELETE\s+FROM\s+\w+\s*;",  # DELETE without WHERE
    r"TRUNCATE\s+TABLE",
    # System-level dangers
    r"chmod\s+777",
    r":()\{.*\|.*&\s*\};:",  # Fork bomb
    r"mkfs\.",
    r"dd\s+if=.*of=/dev/",
]

# ---------------------------------------------------------------------------
# Protected files — cannot be deleted or overwritten via tools
# ---------------------------------------------------------------------------

PROTECTED_FILES = [
    ".env",
    "credentials.json",
    "token.json",
    "setup_config.yaml",
    "CLAUDE.md",
    "memory/MEMORY.md",
    ".claude/hooks/pre_tool_guard.py",
    ".claude/settings.local.json",
]

# ---------------------------------------------------------------------------
# Secret exposure patterns — block commands that would leak credentials
# ---------------------------------------------------------------------------

SECRET_EXPOSURE_PATTERNS = [
    # Direct echo/print of secrets
    r"(echo|printf|cat)\s+.*\b(sk-[a-zA-Z0-9]{20,}|AKIA[A-Z0-9]{16}|"
    r"xoxb-|ghp_|gho_|pcsk_|pplx-|Bearer\s)",
    # Environment variable exposure (standalone commands, not .env filenames)
    r"(?<![.\w/])\b(printenv|env|set)\b(\s|$|\s*\|)",
    r"(echo|printf)\s+.*\$\{?(ANTHROPIC_API_KEY|OPENAI_API_KEY|"
    r"PINECONE_API_KEY|TELEGRAM_BOT_TOKEN|API_KEY|SECRET|PASSWORD)",
    # Python-based credential access and exposure
    r"python3?\s+-c\s+.*os\.(environ|getenv|system).*("
    r"API_KEY|SECRET|TOKEN|PASSWORD|CREDENTIAL)",
    # Network exfiltration of env/secrets
    r"(curl|wget|nc|ncat)\s+.*(\$\{?[A-Z_]*(KEY|TOKEN|SECRET|PASSWORD)|"
    r"/etc/passwd|\.env\b|credentials)",
    # Base64 encoding of secrets (exfiltration technique)
    r"base64\s+.*\.(env|pem|key|credentials)",
]

# ---------------------------------------------------------------------------
# Network exfiltration guards — block suspicious outbound data transfer
# ---------------------------------------------------------------------------

EXFILTRATION_PATTERNS = [
    # Piping file contents to remote
    r"cat\s+\.(env|pem|key)\s*\|",
    r"curl\s+.*-d\s+@\.(env|pem|key)",
    r"curl\s+.*--data.*\.(env|pem|key)",
    # SSH/SCP with credential files
    r"scp\s+.*\.(env|pem|key|credentials)",
]


def check_bash_command(command: str) -> dict:
    """Check a Bash command against all security patterns."""
    # Check blocked commands
    for pattern in BLOCKED_COMMANDS:
        if re.search(pattern, command, re.IGNORECASE):
            return {
                "allow": False,
                "reason": f"BLOCKED: Command matches dangerous pattern. "
                         f"If you need to do this, ask the user for explicit confirmation.",
            }

    # Check protected files for deletion/overwrite
    # Allow "git rm --cached" (untracking is safe — doesn't delete the file)
    for protected in PROTECTED_FILES:
        if protected in command and re.search(r"\b(rm|unlink|mv|>)\b", command):
            if "git rm --cached" in command:
                continue  # Safe: untracking, not deleting
            return {
                "allow": False,
                "reason": f"BLOCKED: Cannot delete or overwrite protected file '{protected}'. "
                         f"This file is critical to the system.",
            }

    # Check secret exposure
    for pattern in SECRET_EXPOSURE_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return {
                "allow": False,
                "reason": "BLOCKED: Command may expose API keys or credentials. "
                         "Use .env and dotenv instead of echoing secrets.",
            }

    # Check exfiltration patterns
    for pattern in EXFILTRATION_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return {
                "allow": False,
                "reason": "BLOCKED: Command appears to transfer credential files externally.",
            }

    return {"allow": True, "reason": ""}


def check_file_write(file_path: str) -> dict:
    """Check if a Write/Edit targets a protected file."""
    for protected in PROTECTED_FILES:
        if file_path.endswith(protected):
            return {
                "allow": False,
                "reason": f"BLOCKED: Direct writes to '{protected}' are not allowed. "
                         f"Use setup.py or manual editing.",
            }
    return {"allow": True, "reason": ""}


def main():
    """Read hook input from stdin, check the command, exit appropriately."""
    try:
        raw = sys.stdin.read()
        if not raw:
            sys.exit(0)

        data = json.loads(raw)
        tool_name = data.get("tool_name", "")
        tool_input = data.get("tool_input", {})

        # Check Bash commands
        if tool_name == "Bash":
            command = tool_input.get("command", "")
            if not command:
                sys.exit(0)

            result = check_bash_command(command)
            if not result["allow"]:
                print(result["reason"])
                sys.exit(2)

        # Check file writes
        elif tool_name in ("Write", "Edit"):
            file_path = tool_input.get("file_path", "")
            result = check_file_write(file_path)
            if not result["allow"]:
                print(result["reason"])
                sys.exit(2)

        sys.exit(0)

    except json.JSONDecodeError:
        sys.exit(0)  # Can't parse = allow (don't break things)
    except Exception:
        sys.exit(0)  # Hooks should never crash Claude — fail-open


if __name__ == "__main__":
    main()
