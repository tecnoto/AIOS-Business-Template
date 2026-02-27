#!/usr/bin/env python3
"""
Serve Dashboard — Simple HTTP server with auto-regeneration.

Serves the dashboard HTML and regenerates it periodically.

Usage:
    python3 .claude/skills/dashboard/scripts/serve_dashboard.py
    python3 .claude/skills/dashboard/scripts/serve_dashboard.py --port 8080
"""

import http.server
import os
import sys
import threading
import time
from pathlib import Path


def _find_root():
    path = Path(__file__).resolve().parent
    while path != path.parent:
        if (path / "CLAUDE.md").exists() or (path / "setup_config.yaml").exists():
            return path
        path = path.parent
    return Path.cwd()


PROJECT_ROOT = _find_root()
DASHBOARD_DIR = PROJECT_ROOT / "dashboard"
REFRESH_INTERVAL = 60  # seconds


def regenerate():
    """Run the dashboard generator."""
    gen_script = PROJECT_ROOT / ".claude" / "skills" / "dashboard" / "scripts" / "generate_dashboard.py"
    os.system(f"{sys.executable} {gen_script} --no-open")


def auto_refresh():
    """Periodically regenerate the dashboard."""
    while True:
        time.sleep(REFRESH_INTERVAL)
        try:
            regenerate()
            print(f"[{time.strftime('%H:%M:%S')}] Dashboard regenerated")
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] Regeneration error: {e}")


def main():
    port = 8000
    if "--port" in sys.argv:
        idx = sys.argv.index("--port")
        if idx + 1 < len(sys.argv):
            port = int(sys.argv[idx + 1])

    # Generate initial dashboard
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    regenerate()

    # Start auto-refresh thread
    refresh_thread = threading.Thread(target=auto_refresh, daemon=True)
    refresh_thread.start()

    # Serve
    os.chdir(str(DASHBOARD_DIR))
    handler = http.server.SimpleHTTPRequestHandler
    server = http.server.HTTPServer(("", port), handler)

    print(f"\nDashboard server running at http://localhost:{port}")
    print(f"Auto-refreshing every {REFRESH_INTERVAL}s")
    print("Press Ctrl+C to stop\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()


if __name__ == "__main__":
    main()
