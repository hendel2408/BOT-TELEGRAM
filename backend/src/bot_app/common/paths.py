from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[3]
REPO_ROOT = BACKEND_DIR.parent
SRC_DIR = BACKEND_DIR / "src"
PACKAGE_DIR = SRC_DIR / "bot_app"
DATA_DIR = BACKEND_DIR / "data"
ENV_PATH = BACKEND_DIR / ".env"
HISTORICO_DB_PATH = DATA_DIR / "historico.db"
IP_LIVRE_PATH = DATA_DIR / "ip_livre.txt"
FRONTEND_DIR = REPO_ROOT / "frontend"
FRONTEND_DIST_DIR = FRONTEND_DIR / "dist"


def ensure_runtime_dirs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
