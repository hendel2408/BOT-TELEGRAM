import os

from flask import Flask, jsonify, request, send_from_directory

from bot_app.automations.bluepex import liberar_visitante
from bot_app.automations.consultor_cs import liberar_consultor
from bot_app.common.paths import FRONTEND_DIST_DIR
from bot_app.services.history_store import fetch_recent_history, init_history_store
from bot_app.services.job_queue import snapshot_queue, submit_job


APP_HOST = os.getenv("PAINEL_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("PAINEL_PORT", "5000"))
SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "painel-local-altere-esta-chave")

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY

def snapshot_estado():
    estado_fila = snapshot_queue()
    estado_fila["historico"] = fetch_recent_history(limit=20)
    return estado_fila


def tipo_legivel(tipo):
    if tipo == "bluepex":
        return "BluePex"
    if tipo == "consultor":
        return "Consultor"
    return tipo


def request_payload():
    if request.is_json:
        return request.get_json(silent=True) or {}
    return request.form


def response_payload(ticket, tipo, nome):
    if ticket["position"] == 0:
        mensagem = f"Liberacao {tipo_legivel(tipo)} iniciada para {nome}."
        nivel = "ok"
    else:
        mensagem = (
            f"Liberacao {tipo_legivel(tipo)} adicionada na fila para {nome}. "
            f"Posicao: {ticket['position']}."
        )
        nivel = "aviso"

    return jsonify(
        {
            "ok": True,
            "message": mensagem,
            "level": nivel,
            "ticket": {"job_id": ticket["job_id"], "position": ticket["position"]},
            "state": snapshot_estado(),
        }
    )


@app.get("/")
@app.get("/<path:path>")
def index(path="index.html"):
    frontend_path = FRONTEND_DIST_DIR / path

    if FRONTEND_DIST_DIR.exists() and frontend_path.is_file():
        return send_from_directory(FRONTEND_DIST_DIR, path)

    if FRONTEND_DIST_DIR.exists():
        return send_from_directory(FRONTEND_DIST_DIR, "index.html")

    return (
        jsonify(
            {
                "ok": False,
                "message": "Frontend nao encontrado. Rode 'npm install' e 'npm run build' dentro da pasta frontend."
            }
        ),
        503,
    )


@app.post("/jobs/bluepex")
def iniciar_bluepex():
    payload = request_payload()
    nome = (payload.get("nome") or "").strip()
    mac = (payload.get("mac") or "").strip()

    if not nome or not mac:
        mensagem = "Informe nome e MAC para iniciar a liberacao BluePex."
        return jsonify({"ok": False, "message": mensagem}), 400

    ticket = submit_job(
        "bluepex",
        "painel",
        {"nome": nome, "mac": mac},
        lambda: liberar_visitante(nome, mac),
    )

    return response_payload(ticket, "bluepex", nome)


@app.post("/jobs/consultor")
def iniciar_consultor():
    payload = request_payload()
    nome = (payload.get("nome_consultor") or payload.get("nome") or "").strip()
    data_limite = (payload.get("data_limite") or "").strip()

    if not nome or not data_limite:
        mensagem = "Informe consultor e data limite para iniciar a automacao."
        return jsonify({"ok": False, "message": mensagem}), 400

    ticket = submit_job(
        "consultor",
        "painel",
        {"nome": nome, "data_limite": data_limite},
        lambda: liberar_consultor(nome, data_limite),
    )

    return response_payload(ticket, "consultor", nome)


@app.get("/api/status")
def api_status():
    return jsonify(snapshot_estado())


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


def run_web_server():
    init_history_store()
    app.run(host=APP_HOST, port=APP_PORT, debug=False, use_reloader=False, threaded=True)


if __name__ == "__main__":
    run_web_server()
