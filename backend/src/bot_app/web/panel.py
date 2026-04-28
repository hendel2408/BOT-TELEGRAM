import os
import ipaddress

from flask import Flask, jsonify, request, send_from_directory, session

from bot_app.automations.bluepex import liberar_visitante
from bot_app.automations.consultor_cs import liberar_consultor
from bot_app.common.paths import FRONTEND_DIST_DIR
from bot_app.services.history_store import fetch_recent_history, init_history_store
from bot_app.services.job_queue import snapshot_queue, submit_job


APP_HOST = os.getenv("PAINEL_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("PAINEL_PORT", "5000"))
SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "painel-local-altere-esta-chave")
PAINEL_LOGIN_USUARIO = os.getenv("PAINEL_LOGIN_USUARIO", "admin")
PAINEL_LOGIN_SENHA = os.getenv("PAINEL_LOGIN_SENHA", "gcv@acesso")
SESSION_AUTH_KEY = "painel_auth_ok"
SESSION_USER_KEY = "painel_auth_user"
PAINEL_INTERNO_APENAS = os.getenv("PAINEL_INTERNO_APENAS", "1").lower() not in {
    "0",
    "false",
    "no",
    "off",
}
PAINEL_CONFIAR_PROXY = os.getenv("PAINEL_CONFIAR_PROXY", "0").lower() in {
    "1",
    "true",
    "yes",
    "on",
}

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


def _ip_cliente():
    if PAINEL_CONFIAR_PROXY:
        forwarded_for = (request.headers.get("X-Forwarded-For") or "").strip()
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

    return (request.remote_addr or "").strip()


def _ip_interno(ip_texto):
    try:
        ip = ipaddress.ip_address(ip_texto)
    except ValueError:
        return False

    return ip.is_loopback or ip.is_private or ip.is_link_local


def _autenticado():
    return bool(session.get(SESSION_AUTH_KEY))


def _resposta_nao_autorizado():
    return (
        jsonify(
            {
                "ok": False,
                "message": "Nao autenticado. Faca login para acessar o painel.",
            }
        ),
        401,
    )


@app.before_request
def bloquear_acesso_externo():
    if not PAINEL_INTERNO_APENAS:
        return None

    if _ip_interno(_ip_cliente()):
        return None

    return (
        jsonify(
            {
                "ok": False,
                "message": "Acesso externo bloqueado. Painel disponivel apenas na rede interna.",
            }
        ),
        403,
    )


@app.before_request
def exigir_login_para_api():
    rota = (request.path or "").strip()

    if rota.startswith("/api/") or rota.startswith("/jobs/"):
        if not _autenticado():
            return _resposta_nao_autorizado()

    return None

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


@app.post("/auth/login")
def auth_login():
    payload = request_payload()
    login = (payload.get("login") or payload.get("usuario") or "").strip()
    senha = (payload.get("senha") or payload.get("password") or "").strip()

    if login != PAINEL_LOGIN_USUARIO or senha != PAINEL_LOGIN_SENHA:
        return jsonify({"ok": False, "message": "Login ou senha invalidos."}), 401

    session.clear()
    session[SESSION_AUTH_KEY] = True
    session[SESSION_USER_KEY] = PAINEL_LOGIN_USUARIO

    return jsonify(
        {
            "ok": True,
            "authenticated": True,
            "user": PAINEL_LOGIN_USUARIO,
            "message": "Login realizado com sucesso.",
        }
    )


@app.post("/auth/logout")
def auth_logout():
    session.clear()
    return jsonify({"ok": True, "authenticated": False, "message": "Sessao encerrada."})


@app.get("/auth/me")
def auth_me():
    if not _autenticado():
        return jsonify({"ok": True, "authenticated": False, "user": None})

    return jsonify(
        {
            "ok": True,
            "authenticated": True,
            "user": session.get(SESSION_USER_KEY),
        }
    )


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
