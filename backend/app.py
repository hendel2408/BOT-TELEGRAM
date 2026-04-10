from pathlib import Path
import sys


BACKEND_DIR = Path(__file__).resolve().parent
SRC_DIR = BACKEND_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from bot_app.web.panel import run_web_server


if __name__ == "__main__":
    run_web_server()
