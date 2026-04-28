import itertools
import multiprocessing as mp
import threading
import time
from collections import deque
from datetime import datetime

from bot_app.services.history_store import append_history_entry, init_history_store


_LOCK = threading.Lock()
_COND = threading.Condition(_LOCK)
_JOB_IDS = itertools.count(1)
_CURRENT_JOB = None
_PENDING_JOBS = deque()
_WORKER_STARTED = False
CANCEL_CHECK_INTERVAL_S = 0.25


def _agora_iso():
    return datetime.now().isoformat(timespec="seconds")


def _agora_humano():
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")


def _public_job(job):
    if not job:
        return None

    return {
        "id": job["id"],
        "tipo": job["tipo"],
        "origem": job["origem"],
        "status": job["status"],
        "sucesso": job.get("sucesso"),
        "mensagem": job.get("mensagem"),
        "dados": dict(job.get("dados", {})),
        "resultado": dict(job.get("resultado", {})),
        "inicio_iso": job.get("inicio_iso"),
        "inicio_humano": job.get("inicio_humano"),
        "fim_iso": job.get("fim_iso"),
        "fim_humano": job.get("fim_humano"),
    }


def _registrar_historico(job):
    append_history_entry(_public_job(job))


def _executar_automacao(tipo, dados):
    if tipo == "bluepex":
        from bot_app.automations.bluepex import liberar_visitante

        return liberar_visitante(dados.get("nome", ""), dados.get("mac", ""))

    if tipo == "consultor":
        from bot_app.automations.consultor_cs import liberar_consultor

        return liberar_consultor(dados.get("nome", ""), dados.get("data_limite", ""))

    raise ValueError(f"Tipo de automacao invalido: {tipo}")


def _job_process_target(tipo, dados, result_queue):
    try:
        resultado = _executar_automacao(tipo, dados)

        if isinstance(resultado, dict):
            payload = resultado
        else:
            payload = {
                "sucesso": False,
                "mensagem": "Automacao finalizou sem retorno valido.",
            }
    except Exception as exc:
        payload = {
            "sucesso": False,
            "mensagem": f"Erro inesperado: {exc}",
        }

    try:
        result_queue.put(payload)
    except Exception:
        pass


def _finalizar_job(job, status, sucesso, mensagem, resultado):
    global _CURRENT_JOB

    with _COND:
        job["status"] = status
        job["sucesso"] = sucesso
        job["mensagem"] = mensagem
        job["resultado"] = resultado
        job["fim_iso"] = _agora_iso()
        job["fim_humano"] = _agora_humano()
        job["event"].set()
        _CURRENT_JOB = None

    _registrar_historico(job)


def _cancelar_job_na_fila(job):
    job["status"] = "Cancelado"
    job["sucesso"] = False
    job["mensagem"] = "Cancelado antes de iniciar."
    job["resultado"] = {
        "sucesso": False,
        "mensagem": "Cancelado antes de iniciar.",
    }
    job["fim_iso"] = _agora_iso()
    job["fim_humano"] = _agora_humano()
    job["event"].set()


def _worker_loop():
    init_history_store()

    while True:
        with _COND:
            while not _PENDING_JOBS:
                _COND.wait()

            job = _PENDING_JOBS.popleft()
            job["status"] = "Executando"
            job["mensagem"] = "Automacao em andamento."
            job["cancel_requested"] = False
            _CURRENT_JOB = job

        result_queue = None
        process = None

        try:
            ctx = mp.get_context("spawn")
            result_queue = ctx.Queue(maxsize=1)
            process = ctx.Process(
                target=_job_process_target,
                args=(job["tipo"], dict(job["dados"]), result_queue),
            )
            process.start()

            with _COND:
                job["process"] = process

            while True:
                with _COND:
                    cancel_requested = bool(job.get("cancel_requested"))

                if cancel_requested:
                    if process.is_alive():
                        process.terminate()
                    process.join(timeout=5)

                    resultado = {
                        "sucesso": False,
                        "mensagem": "Execucao cancelada manualmente.",
                    }
                    _finalizar_job(
                        job,
                        status="Cancelado",
                        sucesso=False,
                        mensagem=resultado["mensagem"],
                        resultado=resultado,
                    )
                    break

                if not process.is_alive():
                    process.join(timeout=2)

                    try:
                        resultado = result_queue.get_nowait()
                    except Exception:
                        resultado = {
                            "sucesso": False,
                            "mensagem": "Processo finalizou sem retorno.",
                        }

                    sucesso = bool(resultado.get("sucesso"))
                    mensagem = resultado.get("mensagem") or "Automacao finalizada."
                    status = "Concluido" if sucesso else "Falha"

                    _finalizar_job(
                        job,
                        status=status,
                        sucesso=sucesso,
                        mensagem=mensagem,
                        resultado=resultado,
                    )
                    break

                time.sleep(CANCEL_CHECK_INTERVAL_S)

        except Exception as exc:
            resultado = {
                "sucesso": False,
                "mensagem": f"Erro inesperado no worker: {exc}",
            }
            _finalizar_job(
                job,
                status="Falha",
                sucesso=False,
                mensagem=resultado["mensagem"],
                resultado=resultado,
            )
        finally:
            with _COND:
                job["process"] = None

            if result_queue is not None:
                try:
                    result_queue.close()
                except Exception:
                    pass


def init_job_queue():
    global _WORKER_STARTED

    with _COND:
        if _WORKER_STARTED:
            return

        worker = threading.Thread(target=_worker_loop, daemon=True)
        worker.start()
        _WORKER_STARTED = True


def submit_job(tipo, origem, dados):
    init_job_queue()

    with _COND:
        job = {
            "id": next(_JOB_IDS),
            "tipo": tipo,
            "origem": origem,
            "status": "Na fila",
            "sucesso": None,
            "mensagem": "Aguardando execucao.",
            "dados": dados,
            "resultado": {},
            "inicio_iso": _agora_iso(),
            "inicio_humano": _agora_humano(),
            "fim_iso": None,
            "fim_humano": None,
            "event": threading.Event(),
            "cancel_requested": False,
            "process": None,
        }

        position = len(_PENDING_JOBS) + (1 if _CURRENT_JOB else 0)
        _PENDING_JOBS.append(job)
        _COND.notify()

    return {
        "job_id": job["id"],
        "position": position,
        "event": job["event"],
        "job": job,
    }


def wait_for_job(ticket):
    ticket["event"].wait()
    return dict(ticket["job"].get("resultado", {}))


def cancel_all_jobs():
    init_job_queue()

    cancelados_fila = []
    execucao_cancelada = None

    with _COND:
        while _PENDING_JOBS:
            job = _PENDING_JOBS.popleft()
            _cancelar_job_na_fila(job)
            cancelados_fila.append(job)

        if _CURRENT_JOB is not None and _CURRENT_JOB.get("status") == "Executando":
            _CURRENT_JOB["cancel_requested"] = True
            execucao_cancelada = _CURRENT_JOB["id"]

    for job in cancelados_fila:
        _registrar_historico(job)

    return {
        "pending_cancelled": len(cancelados_fila),
        "running_cancel_requested": execucao_cancelada is not None,
        "running_job_id": execucao_cancelada,
    }


def snapshot_queue():
    init_job_queue()

    with _COND:
        return {
            "ocupado": _CURRENT_JOB is not None,
            "job_atual": _public_job(_CURRENT_JOB),
            "fila": [_public_job(job) for job in _PENDING_JOBS],
        }
