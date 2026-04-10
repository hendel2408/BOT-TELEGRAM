from pathlib import Path
import sys
import threading

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bot_app.telegram_bot import run_telegram_bot
from bot_app.web.panel import run_web_server


def main():
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()

    run_telegram_bot()


if __name__ == "__main__":
    main()
