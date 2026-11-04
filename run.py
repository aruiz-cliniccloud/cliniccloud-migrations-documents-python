import os
import signal
import sys
from dotenv import load_dotenv
from app import create_app

load_dotenv()

app = create_app()


def _handle_shutdown(signum, frame):
    print("\n  Server shutting down cleanly.")
    sys.exit(0)


signal.signal(signal.SIGTERM, _handle_shutdown)


if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 8080))
    debug = os.getenv("FLASK_ENV", "development") == "development"

    print(f"\n  Server running → http://{host}:{port}")
    print(f"  Health check  → http://{host}:{port}/health")
    print("  Stop with Ctrl+C or: make stop\n")

    app.run(host=host, port=port, debug=debug)
