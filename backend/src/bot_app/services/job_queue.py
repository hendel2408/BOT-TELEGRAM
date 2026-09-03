import itertools
import threading
from collections import deque
from datetime import datetime

from bot_app.services.history_store import append_history_entry, init_history_store


_LOCK = threading.Lock()
_COND = threading.Condition(_LOCK)
_JOB_IDS = itertools.count(1)
_CURRENT_JOB = None
_PENDING_JOBS = deque()
_WORKER_STARTED = False


def _agora_iso():
    return datetime.now().isoformat(timespec="seconds")


def _agora_humano():
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")


def _public_job(job):
    if not job:
        return None

    eventos = list(job.get("eventos", []))

    return {
        "id": job["id"],
        "tipo": job["tipo"],
        "origem": job["origem"],
        "status": job["status"],
        "sucesso": job.get("sucesso"),
        "mensagem": job.get("mensagem"),
        "dados": dict(job.get("dados", {})),
        "resultado": dict(job.get("resultado", {})),
        "eventos": eventos,
        "inicio_iso": job.get("inicio_iso"),
        "inicio_humano": job.get("inicio_humano"),
        "fim_iso": job.get("fim_iso"),
        "fim_humano": job.get("fim_humano"),
    }


def _registrar_historico(job):
    append_history_entry(_public_job(job))


def _worker_loop():
    global _CURRENT_JOB

    init_history_store()

    while True:
        with _COND:
            while not _PENDING_JOBS:
                _COND.wait()

            job = _PENDING_JOBS.popleft()
            _CURRENT_JOB = job
            job["status"] = "Executando"
            job["mensagem"] = "Automacao em andamento."

        try:
            resultado = job["runner"]()
            sucesso = bool(resultado.get("sucesso"))
            mensagem = resultado.get("mensagem") or "Automacao finalizada."
        except Exception as exc:
            resultado = {"sucesso": False, "mensagem": f"Erro inesperado: {exc}"}
            sucesso = False
            mensagem = resultado["mensagem"]

        with _COND:
            eventos = list(job.get("eventos", []))
            if eventos:
                resultado = dict(resultado)
                resultado["eventos"] = eventos

            job["status"] = "Concluido" if sucesso else "Falha"
            job["sucesso"] = sucesso
            job["mensagem"] = mensagem
            job["resultado"] = resultado
            job["fim_iso"] = _agora_iso()
            job["fim_humano"] = _agora_humano()
            _CURRENT_JOB = None
            job["event"].set()

        _registrar_historico(job)


def init_job_queue():
    global _WORKER_STARTED

    with _COND:
        if _WORKER_STARTED:
            return

        worker = threading.Thread(target=_worker_loop, daemon=True)
        worker.start()
        _WORKER_STARTED = True


def submit_job(tipo, origem, dados, runner):
    init_job_queue()

    with _COND:
        job, position = _enqueue_job_locked(tipo, origem, dados, runner)

    return {
        "accepted": True,
        "job_id": job["id"],
        "position": position,
        "event": job["event"],
        "job": job,
    }


def submit_job_once(tipo, origem, dados, runner):
    init_job_queue()

    with _COND:
        if _job_tipo_em_andamento_locked(tipo):
            return {
                "accepted": False,
                "job_id": None,
                "position": None,
                "event": None,
                "job": None,
            }

        job, position = _enqueue_job_locked(tipo, origem, dados, runner)

    return {
        "accepted": True,
        "job_id": job["id"],
        "position": position,
        "event": job["event"],
        "job": job,
    }


def update_current_job_message(tipo, mensagem):
    mensagem = str(mensagem or "").strip()
    if not mensagem:
        return False

    evento = {
        "mensagem": mensagem,
        "momento_iso": _agora_iso(),
        "momento_humano": _agora_humano(),
    }

    with _COND:
        if not _CURRENT_JOB:
            return False

        if tipo and _CURRENT_JOB["tipo"] != tipo:
            return False

        _CURRENT_JOB["mensagem"] = mensagem
        _CURRENT_JOB.setdefault("eventos", []).append(evento)
        _CURRENT_JOB.setdefault("resultado", {})["eventos"] = list(
            _CURRENT_JOB["eventos"]
        )
        return True


def _job_tipo_em_andamento_locked(tipo):
    if _CURRENT_JOB and _CURRENT_JOB["tipo"] == tipo:
        return True

    return any(job["tipo"] == tipo for job in _PENDING_JOBS)


def _enqueue_job_locked(tipo, origem, dados, runner):
    job = {
        "id": next(_JOB_IDS),
        "tipo": tipo,
        "origem": origem,
        "status": "Na fila",
        "sucesso": None,
        "mensagem": "Aguardando execucao.",
        "dados": dados,
        "resultado": {},
        "eventos": [],
        "inicio_iso": _agora_iso(),
        "inicio_humano": _agora_humano(),
        "fim_iso": None,
        "fim_humano": None,
        "runner": runner,
        "event": threading.Event(),
    }

    position = len(_PENDING_JOBS) + (1 if _CURRENT_JOB else 0)
    _PENDING_JOBS.append(job)
    _COND.notify()

    return job, position


def wait_for_job(ticket):
    ticket["event"].wait()
    return dict(ticket["job"].get("resultado", {}))


def snapshot_queue():
    init_job_queue()

    with _COND:
        return {
            "ocupado": _CURRENT_JOB is not None,
            "job_atual": _public_job(_CURRENT_JOB),
            "fila": [_public_job(job) for job in _PENDING_JOBS],
        }
