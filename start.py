"""
start.py — Launch FastAPI + Streamlit with a single command.

    python start.py

Ctrl+C shuts down both processes cleanly.
"""

import subprocess
import sys
import signal
import time

API_HOST  = "127.0.0.1"
API_PORT  = 8000
UI_PORT   = 8501

def main():
    python = sys.executable

    api_cmd = [
        python, "-m", "uvicorn", "api:app",
        "--host", API_HOST,
        "--port", str(API_PORT),
        "--reload",
    ]

    ui_cmd = [
        python, "-m", "streamlit", "run", "ui.py",
        "--server.port", str(UI_PORT),
        "--server.headless", "true",
    ]

    print(f"\n🚀  Starting EmerClinic Support Agent")
    print(f"    API  →  http://{API_HOST}:{API_PORT}")
    print(f"    UI   →  http://localhost:{UI_PORT}")
    print(f"\n    Press Ctrl+C to stop both services.\n")

    api_proc = subprocess.Popen(api_cmd)
    # Small delay so the API is up before Streamlit opens in the browser
    time.sleep(1.5)
    ui_proc  = subprocess.Popen(ui_cmd)

    def shutdown(sig, frame):
        print("\n\nShutting down...")
        ui_proc.terminate()
        api_proc.terminate()
        ui_proc.wait()
        api_proc.wait()
        print("Done.")
        sys.exit(0)

    signal.signal(signal.SIGINT,  shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # Keep the launcher alive while children run
    api_proc.wait()


if __name__ == "__main__":
    main()
