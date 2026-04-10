import json
import sqlite3
import threading

from bot_app.common.paths import HISTORICO_DB_PATH, ensure_runtime_dirs

DB_PATH = HISTORICO_DB_PATH
LOCK = threading.Lock()


def _connect():
    ensure_runtime_dirs()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_history_store():
    with LOCK:
        conn = _connect()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS job_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo TEXT NOT NULL,
                    origem TEXT NOT NULL,
                    status TEXT NOT NULL,
                    sucesso INTEGER,
                    mensagem TEXT,
                    dados_json TEXT NOT NULL,
                    resultado_json TEXT NOT NULL,
                    inicio_iso TEXT,
                    inicio_humano TEXT,
                    fim_iso TEXT,
                    fim_humano TEXT
                )
                """
            )
            conn.commit()
        finally:
            conn.close()


def append_history_entry(entry):
    init_history_store()

    with LOCK:
        conn = _connect()
        try:
            conn.execute(
                """
                INSERT INTO job_history (
                    tipo, origem, status, sucesso, mensagem,
                    dados_json, resultado_json, inicio_iso, inicio_humano,
                    fim_iso, fim_humano
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.get("tipo", ""),
                    entry.get("origem", ""),
                    entry.get("status", ""),
                    entry.get("sucesso"),
                    entry.get("mensagem", ""),
                    json.dumps(entry.get("dados", {}), ensure_ascii=False),
                    json.dumps(entry.get("resultado", {}), ensure_ascii=False),
                    entry.get("inicio_iso"),
                    entry.get("inicio_humano"),
                    entry.get("fim_iso"),
                    entry.get("fim_humano"),
                ),
            )
            conn.commit()
        finally:
            conn.close()


def fetch_recent_history(limit=20):
    init_history_store()

    with LOCK:
        conn = _connect()
        try:
            rows = conn.execute(
                """
                SELECT id, tipo, origem, status, sucesso, mensagem, dados_json,
                       resultado_json, inicio_iso, inicio_humano, fim_iso, fim_humano
                FROM job_history
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        finally:
            conn.close()

    items = []
    for row in rows:
        items.append(
            {
                "id": row["id"],
                "tipo": row["tipo"],
                "origem": row["origem"],
                "status": row["status"],
                "sucesso": None if row["sucesso"] is None else bool(row["sucesso"]),
                "mensagem": row["mensagem"],
                "dados": json.loads(row["dados_json"] or "{}"),
                "resultado": json.loads(row["resultado_json"] or "{}"),
                "inicio_iso": row["inicio_iso"],
                "inicio_humano": row["inicio_humano"],
                "fim_iso": row["fim_iso"],
                "fim_humano": row["fim_humano"],
            }
        )

    return items
