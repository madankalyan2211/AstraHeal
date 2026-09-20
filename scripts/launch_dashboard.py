#!/usr/bin/env python3
"""AstraHeal Unified Research Mission Operations Center (MOC) Launcher.

Starts the FastAPI + WebSocket backend and opens the dashboard in the default browser.
Supports real-time digital twin streaming, Paper 1, Paper 2, and Paper 3.
"""

import os
import sys
import time
import webbrowser
from pathlib import Path

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import uvicorn

def main():
    port = 8000
    url = f"http://127.0.0.1:{port}"
    
    print("=" * 75)
    print("🚀 ASTRAHEAL RESEARCH MISSION OPERATIONS CENTER (MOC)")
    print("Papers 1, 2, and 3 Unified Real-Time Telemetry & Safety Gating Suite")
    print(f"Target URL: {url}")
    print("=" * 75)
    
    # Open browser automatically after a short delay
    def open_browser():
        time.sleep(1.2)
        print(f"Opening browser at {url}...")
        webbrowser.open(url)

    import threading
    threading.Thread(target=open_browser, daemon=True).start()

    # Run Uvicorn server
    uvicorn.run("dashboard.server:app", host="127.0.0.1", port=port, reload=False, log_level="info")

if __name__ == "__main__":
    main()
