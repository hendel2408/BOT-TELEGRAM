import ctypes
from ctypes import wintypes
import importlib.util
import os
import re
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional

from dotenv import load_dotenv

from bot_app.common.paths import (
    ENV_PATH,
    GCV_PRINTS_DIR,
    PACKAGE_DIR,
    REPO_ROOT,
    ensure_runtime_dirs,
)


load_dotenv(dotenv_path=ENV_PATH, override=True)

PARAR_NOT_FOUND_AFTER_LOGIN_MESSAGE = (
    "⚠️ Não foi possível localizar Parar Robôs após o login."
)
MANUAL_RECOVERY_MESSAGE = (
    "🚨 Os robôs podem estar parados. Faça a recuperação manual."
)
SUCCESS_MESSAGE = "✅ Robôs GCV reiniciados com sucesso e acesso remoto encerrado."
SUCCESS_RDP_X_NOT_FOUND_MESSAGE = (
    "✅ Robôs GCV reiniciados, mas não foi possível localizar o botão X do acesso remoto."
)
SUCCESS_RDP_CONFIRM_FAILED_MESSAGE = (
    "✅ Robôs GCV reiniciados, mas não foi possível confirmar o encerramento do acesso remoto."
)
PROGRESS_OPEN = "🔄 Abrindo acesso aos robôs GCV..."
PROGRESS_STOP = "⏹️ Encerrando os robôs..."
PROGRESS_START = "▶️ Iniciando novamente os robôs..."

DEFAULT_CREDENTIAL_TARGET = "BOT_TELEGRAM_GCV_ROBO_PASSWORD"
EXECUTABLE_NOT_FOUND_MESSAGE = (
    "❌ Não foi encontrado o arquivo ROBO GCV\\csrobogcv (1).exe "
    "na Área de Trabalho deste computador."
)
PASSWORD_TITLE = os.getenv("GCV_PASSWORD_WINDOW_TITLE", "Password")
PASSWORD_TEXT = os.getenv("GCV_PASSWORD_WINDOW_TEXT", "Please enter the password.")
RDP_TITLE_REGEX = os.getenv(
    "GCV_RDP_TITLE_REGEX",
    (
        "Área de Trabalho Remota|Area de Trabalho Remota|"
        "Conexão de Área de Trabalho Remota|Conexao de Area de Trabalho Remota|"
        "Remote Desktop|csrobogcv|GCV"
    ),
)

LOGIN_TIMEOUT_S = int(os.getenv("GCV_LOGIN_TIMEOUT_S", "60"))
DESKTOP_TIMEOUT_S = int(os.getenv("GCV_DESKTOP_TIMEOUT_S", "120"))
STOP_VISUAL_TIMEOUT_S = float(os.getenv("GCV_STOP_VISUAL_TIMEOUT_S", "15"))
VISUAL_POLL_INTERVAL_S = float(os.getenv("GCV_VISUAL_POLL_INTERVAL_S", "0.5"))
MONITORAR_TIMEOUT_S = int(os.getenv("GCV_MONITORAR_TIMEOUT_S", "60"))
RDP_REVEAL_BAR_DELAY_S = float(os.getenv("GCV_RDP_REVEAL_BAR_DELAY_S", "2"))
RDP_CONFIRMATION_TIMEOUT_S = float(os.getenv("GCV_RDP_CONFIRMATION_TIMEOUT_S", "10"))
RDP_CLOSE_VERIFY_TIMEOUT_S = float(os.getenv("GCV_RDP_CLOSE_VERIFY_TIMEOUT_S", "10"))
RDP_TOP_BAR_SEARCH_HEIGHT = int(os.getenv("GCV_RDP_TOP_BAR_SEARCH_HEIGHT", "120"))
POLL_INTERVAL_S = float(os.getenv("GCV_POLL_INTERVAL_S", "1"))
IMAGE_CONFIDENCE = float(os.getenv("GCV_IMAGE_CONFIDENCE", "0.86"))
IMAGE_MAX_MEAN_DIFF = float(os.getenv("GCV_IMAGE_MAX_MEAN_DIFF", "35"))
IMAGE_SCALE_VARIATIONS = os.getenv("GCV_IMAGE_SCALE_VARIATIONS", "")
IMAGE_SCALE_MIN = float(os.getenv("GCV_IMAGE_SCALE_MIN", "0.65"))
IMAGE_SCALE_MAX = float(os.getenv("GCV_IMAGE_SCALE_MAX", "1.50"))
IMAGE_SCALE_STEP = float(os.getenv("GCV_IMAGE_SCALE_STEP", "0.05"))
IMAGE_BASE_RDP_WIDTH = float(os.getenv("GCV_IMAGE_BASE_RDP_WIDTH", "1920"))
IMAGE_BASE_RDP_HEIGHT = float(os.getenv("GCV_IMAGE_BASE_RDP_HEIGHT", "1080"))
GCV_ASSETS_DIR = PACKAGE_DIR / "assets" / "gcv"
DEFAULT_PARAR_ROBOS_IMAGE = GCV_ASSETS_DIR / "parar_robos.png"
DEFAULT_MONITORAR_ROBOS_IMAGE = GCV_ASSETS_DIR / "monitorar_robos.png"
DEFAULT_AVISO_ROBOS_ENCERRADOS_IMAGE = (
    GCV_ASSETS_DIR / "aviso_robos_encerrados.png"
)
DEFAULT_TERMINAL_PARAR_ROBOS_IMAGE = GCV_ASSETS_DIR / "terminal_parar_robos.png"
DEFAULT_FECHAR_TERMINAL_PARAR_ROBOS_IMAGE = (
    GCV_ASSETS_DIR / "fechar_terminal_parar_robos.png"
)
DEFAULT_FECHAR_RDP_NORMAL_IMAGE = GCV_ASSETS_DIR / "fechar_rdp_normal.png"
DEFAULT_FECHAR_RDP_NORMAL_SERVIDOR_IMAGE = (
    GCV_ASSETS_DIR / "fechar_rdp_normal_servidor.png"
)
DEFAULT_FECHAR_RDP_NORMAL_IMAGES = (
    DEFAULT_FECHAR_RDP_NORMAL_IMAGE,
    DEFAULT_FECHAR_RDP_NORMAL_SERVIDOR_IMAGE,
)
DEFAULT_FECHAR_RDP_HOVER_IMAGE = GCV_ASSETS_DIR / "fechar_rdp_hover.png"
DEFAULT_CONFIRMACAO_DESCONEXAO_RDP_IMAGE = (
    GCV_ASSETS_DIR / "confirmacao_desconexao_rdp.png"
)
DEFAULT_OK_DESCONEXAO_RDP_IMAGE = GCV_ASSETS_DIR / "ok_desconexao_rdp.png"
AVISO_CLOSE_X_RATIO = float(os.getenv("GCV_AVISO_CLOSE_X_RATIO", "0.9597989949748744"))
AVISO_CLOSE_Y_RATIO = float(os.getenv("GCV_AVISO_CLOSE_Y_RATIO", "0.34210526315789475"))

_RESTART_LOCK = threading.Lock()
GCV_DEPENDENCIES = ("pyautogui", "pywinauto", "cv2")
SW_SHOW = 5
SW_RESTORE = 9
SW_MAXIMIZE = 3


@dataclass
class ImageMatch:
    left: int
    top: int
    width: int
    height: int
    confidence: Optional[float] = None
    mean_diff: Optional[float] = None
    scale: Optional[float] = None
    template_name: Optional[str] = None

    @property
    def center(self):
        return (
            self.left + self.width // 2,
            self.top + self.height // 2,
        )

    @property
    def right(self):
        return self.left + self.width

    @property
    def bottom(self):
        return self.top + self.height


@dataclass
class GcvConfig:
    exe_path: Path
    password: str
    parar_icon_images: List[Path]
    monitorar_icon_images: List[Path]
    aviso_robos_encerrados_images: List[Path]
    terminal_parar_robos_images: List[Path]
    fechar_terminal_parar_robos_images: List[Path]
    fechar_rdp_normal_images: List[Path]
    fechar_rdp_hover_images: List[Path]
    confirmacao_desconexao_rdp_images: List[Path]
    ok_desconexao_rdp_images: List[Path]


@dataclass
class GcvRuntimeState:
    robos_podem_estar_parados: bool = False
    fluxo_sucesso: bool = False
    rdp_window: Optional[object] = None
    rdp_hwnd: Optional[int] = None
    manter_rdp_visivel: bool = False


@dataclass
class RdpCloseResult:
    fechada: bool
    mensagem: str
    codigo: str
    screenshot_path: Optional[str] = None
    manter_rdp_visivel: bool = False


class GcvAutomationError(RuntimeError):
    def __init__(self, message, code="erro", screenshot=False):
        super().__init__(message)
        self.message = message
        self.code = code
        self.screenshot = screenshot


def reiniciar_robos_gcv(notificar: Optional[Callable[[str], None]] = None):
    if not _RESTART_LOCK.acquire(blocking=False):
        return {
            "sucesso": False,
            "mensagem": "Ja existe um reinicio dos robos GCV em andamento.",
            "codigo": "bloqueado",
            "screenshot_path": None,
        }

    janela_anterior = _obter_janela_ativa_hwnd()
    state = GcvRuntimeState()

    try:
        resultado = _executar_reinicio(notificar, state)
        state.fluxo_sucesso = bool(resultado.get("sucesso"))
        return resultado
    except GcvAutomationError as exc:
        falha_pos_parar = state.robos_podem_estar_parados and not state.fluxo_sucesso
        screenshot_path = (
            _capturar_print(exc.code)
            if exc.screenshot or falha_pos_parar
            else None
        )
        return {
            "sucesso": False,
            "mensagem": (
                _mensagem_recuperacao_manual(exc.message)
                if falha_pos_parar
                else exc.message
            ),
            "codigo": exc.code,
            "screenshot_path": screenshot_path,
        }
    except Exception as exc:
        falha_pos_parar = state.robos_podem_estar_parados and not state.fluxo_sucesso
        screenshot_path = _capturar_print("erro_inesperado")
        return {
            "sucesso": False,
            "mensagem": (
                _mensagem_recuperacao_manual()
                if falha_pos_parar
                else f"Erro inesperado no reinicio dos robos GCV: {exc}"
            ),
            "codigo": "erro_inesperado",
            "screenshot_path": screenshot_path,
        }
    finally:
        if (
            state.manter_rdp_visivel
            or state.robos_podem_estar_parados
            and not state.fluxo_sucesso
        ):
            _manter_rdp_visivel_para_recuperacao(state.rdp_window)
        else:
            _restaurar_janela_anterior(janela_anterior)
        _RESTART_LOCK.release()


def _mensagem_recuperacao_manual(detalhe=None):
    if not detalhe or detalhe == MANUAL_RECOVERY_MESSAGE:
        return MANUAL_RECOVERY_MESSAGE

    if str(detalhe).startswith(MANUAL_RECOVERY_MESSAGE):
        return detalhe

    return f"{MANUAL_RECOVERY_MESSAGE}\n{detalhe}"


def _mensagem_template_nao_localizado(descricao, imagens):
    nomes = ", ".join(path.name for path in imagens)
    if nomes and nomes != descricao:
        return f"Imagem não encontrada: {descricao} ({nomes})."

    return f"Imagem não encontrada: {descricao}."


def diagnosticar_gcv():
    janela_anterior = _obter_janela_ativa_hwnd()

    try:
        dependencias = _diagnosticar_dependencias()
        executavel = _diagnosticar_executavel()
        senha = _diagnosticar_senha()
        sessao = _diagnosticar_sessao_interativa()
        templates = _diagnosticar_templates()

        sucesso = (
            dependencias["ok"]
            and executavel["ok"]
            and senha["ok"]
            and sessao["ok"]
            and templates["parar_robos"]["ok"]
            and templates["monitorar_robos"]["ok"]
            and templates["aviso_robos_encerrados"]["ok"]
            and templates["terminal_parar_robos"]["ok"]
            and templates["fechar_terminal_parar_robos"]["ok"]
            and templates["fechar_rdp_normal"]["ok"]
            and templates["fechar_rdp_hover"]["ok"]
            and templates["confirmacao_desconexao_rdp"]["ok"]
            and templates["ok_desconexao_rdp"]["ok"]
        )

        return {
            "sucesso": sucesso,
            "mensagem": (
                "Diagnostico GCV concluido."
                if sucesso
                else "Diagnostico GCV encontrou pendencias."
            ),
            "dependencias": dependencias,
            "executavel": executavel,
            "senha": senha,
            "sessao": sessao,
            "templates": templates,
        }
    finally:
        _restaurar_janela_anterior(janela_anterior)


def _executar_reinicio(notificar, state):
    config = _carregar_configuracao()

    _enviar_andamento(notificar, PROGRESS_OPEN)
    _validar_sessao_interativa()
    _abrir_executavel(config.exe_path)
    login_window = _aguardar_janela_por_titulo(
        f"^{re.escape(PASSWORD_TITLE)}$",
        LOGIN_TIMEOUT_S,
        "janela de senha",
    )
    _validar_texto_janela(login_window, PASSWORD_TEXT)
    _preencher_senha(login_window, config.password)

    rdp_window = _aguardar_janela_por_titulo(
        RDP_TITLE_REGEX,
        DESKTOP_TIMEOUT_S,
        "Area de Trabalho Remota",
    )
    state.rdp_window = rdp_window
    state.rdp_hwnd = _preparar_janela_remota(rdp_window)
    parar_match, _ = _aguardar_area_trabalho_pronta(rdp_window, config)

    _enviar_andamento(notificar, PROGRESS_STOP)
    _duplo_clique(rdp_window, parar_match, "Parar Robos")
    state.robos_podem_estar_parados = True

    _log("Aguardando 10 segundos após Parar Robôs.")
    time.sleep(10)
    _fechar_template_na_rdp(
        rdp_window,
        config.aviso_robos_encerrados_images,
        "aviso de robôs encerrados",
        AVISO_CLOSE_X_RATIO,
        AVISO_CLOSE_Y_RATIO,
    )
    time.sleep(2)
    _confirmar_template_sumiu_na_rdp(
        rdp_window,
        config.aviso_robos_encerrados_images,
        "aviso de robôs encerrados",
    )
    _fechar_terminal_parar_robos_na_rdp(rdp_window, config)
    _log("Procurando Monitorar Robôs.")

    monitorar_match = _aguardar_icone_monitorar(
        rdp_window,
        config,
        timeout_s=MONITORAR_TIMEOUT_S,
    )

    _enviar_andamento(notificar, PROGRESS_START)
    _duplo_clique(rdp_window, monitorar_match, "Monitorar Robôs")
    state.fluxo_sucesso = True
    _log("Aguardando 5 segundos apos Monitorar Robos.")
    time.sleep(5)
    rdp_close = _fechar_rdp_visualmente(state.rdp_hwnd, config)
    state.manter_rdp_visivel = rdp_close.manter_rdp_visivel

    return {
        "sucesso": True,
        "mensagem": rdp_close.mensagem,
        "codigo": rdp_close.codigo,
        "screenshot_path": rdp_close.screenshot_path,
    }


def _carregar_configuracao():
    exe_path = _resolver_executavel()
    password = _obter_senha()
    parar_icon_images, monitorar_icon_images = _resolver_templates_principais()
    (
        aviso_robos_encerrados_images,
        terminal_parar_robos_images,
        fechar_terminal_parar_robos_images,
    ) = _resolver_templates_pos_parar()
    (
        fechar_rdp_normal_images,
        fechar_rdp_hover_images,
        confirmacao_desconexao_rdp_images,
        ok_desconexao_rdp_images,
    ) = _resolver_templates_fechamento_rdp()

    return GcvConfig(
        exe_path=exe_path,
        password=password,
        parar_icon_images=parar_icon_images,
        monitorar_icon_images=monitorar_icon_images,
        aviso_robos_encerrados_images=aviso_robos_encerrados_images,
        terminal_parar_robos_images=terminal_parar_robos_images,
        fechar_terminal_parar_robos_images=fechar_terminal_parar_robos_images,
        fechar_rdp_normal_images=fechar_rdp_normal_images,
        fechar_rdp_hover_images=fechar_rdp_hover_images,
        confirmacao_desconexao_rdp_images=confirmacao_desconexao_rdp_images,
        ok_desconexao_rdp_images=ok_desconexao_rdp_images,
    )


def _diagnosticar_templates():
    return {
        "parar_robos": _diagnosticar_template(
            "Parar Robôs",
            "GCV_PARAR_ROBOS_IMAGE",
            DEFAULT_PARAR_ROBOS_IMAGE,
        ),
        "monitorar_robos": _diagnosticar_template(
            "Monitorar Robôs",
            "GCV_MONITORAR_ROBOS_IMAGE",
            DEFAULT_MONITORAR_ROBOS_IMAGE,
        ),
        "aviso_robos_encerrados": _diagnosticar_template(
            "Aviso robôs encerrados",
            "GCV_AVISO_ROBOS_ENCERRADOS_IMAGE",
            DEFAULT_AVISO_ROBOS_ENCERRADOS_IMAGE,
        ),
        "terminal_parar_robos": _diagnosticar_template(
            "Terminal Parar Robôs",
            "GCV_TERMINAL_PARAR_ROBOS_IMAGE",
            DEFAULT_TERMINAL_PARAR_ROBOS_IMAGE,
        ),
        "fechar_terminal_parar_robos": _diagnosticar_template(
            "Botao X terminal Parar Robos",
            "GCV_FECHAR_TERMINAL_PARAR_ROBOS_IMAGE",
            DEFAULT_FECHAR_TERMINAL_PARAR_ROBOS_IMAGE,
        ),
        "fechar_rdp_normal": _diagnosticar_template(
            "Fechar RDP normal",
            "GCV_FECHAR_RDP_NORMAL_IMAGE",
            DEFAULT_FECHAR_RDP_NORMAL_IMAGES,
        ),
        "fechar_rdp_hover": _diagnosticar_template(
            "Fechar RDP hover",
            "GCV_FECHAR_RDP_HOVER_IMAGE",
            DEFAULT_FECHAR_RDP_HOVER_IMAGE,
        ),
        "confirmacao_desconexao_rdp": _diagnosticar_template(
            "Confirmacao desconexao RDP",
            "GCV_CONFIRMACAO_DESCONEXAO_RDP_IMAGE",
            DEFAULT_CONFIRMACAO_DESCONEXAO_RDP_IMAGE,
        ),
        "ok_desconexao_rdp": _diagnosticar_template(
            "OK desconexao RDP",
            "GCV_OK_DESCONEXAO_RDP_IMAGE",
            DEFAULT_OK_DESCONEXAO_RDP_IMAGE,
        ),
    }


def _diagnosticar_template(rotulo, env_name, default_path):
    try:
        paths = _resolver_template_padrao_ou_env(rotulo, env_name, default_path)
        detalhes = ", ".join(_caminho_para_log(path) for path in paths)
        return {
            "ok": True,
            "status": "encontrado",
            "mensagem": detalhes,
        }
    except GcvAutomationError as exc:
        return {
            "ok": False,
            "status": "ausente",
            "mensagem": exc.message,
        }
    except Exception as exc:
        return {
            "ok": False,
            "status": "ausente",
            "mensagem": f"Erro ao validar template {rotulo}: {exc}",
    }


def _resolver_templates_principais():
    resultados = {}
    erros = []

    for chave, rotulo, env_name, default_path in (
        (
            "parar_robos",
            "Parar Robôs",
            "GCV_PARAR_ROBOS_IMAGE",
            DEFAULT_PARAR_ROBOS_IMAGE,
        ),
        (
            "monitorar_robos",
            "Monitorar Robôs",
            "GCV_MONITORAR_ROBOS_IMAGE",
            DEFAULT_MONITORAR_ROBOS_IMAGE,
        ),
    ):
        try:
            resultados[chave] = _resolver_template_padrao_ou_env(
                rotulo,
                env_name,
                default_path,
            )
        except GcvAutomationError as exc:
            erros.append(exc.message)

    if erros:
        raise GcvAutomationError(
            " ".join(erros),
            code="template_ausente",
        )

    return resultados["parar_robos"], resultados["monitorar_robos"]


def _resolver_templates_pos_parar():
    resultados = {}
    erros = []

    for chave, rotulo, env_name, default_path in (
        (
            "aviso_robos_encerrados",
            "Aviso robôs encerrados",
            "GCV_AVISO_ROBOS_ENCERRADOS_IMAGE",
            DEFAULT_AVISO_ROBOS_ENCERRADOS_IMAGE,
        ),
        (
            "terminal_parar_robos",
            "Terminal Parar Robôs",
            "GCV_TERMINAL_PARAR_ROBOS_IMAGE",
            DEFAULT_TERMINAL_PARAR_ROBOS_IMAGE,
        ),
        (
            "fechar_terminal_parar_robos",
            "Botao X terminal Parar Robos",
            "GCV_FECHAR_TERMINAL_PARAR_ROBOS_IMAGE",
            DEFAULT_FECHAR_TERMINAL_PARAR_ROBOS_IMAGE,
        ),
    ):
        try:
            resultados[chave] = _resolver_template_padrao_ou_env(
                rotulo,
                env_name,
                default_path,
            )
        except GcvAutomationError as exc:
            erros.append(exc.message)

    if erros:
        raise GcvAutomationError(
            " ".join(erros),
            code="template_ausente",
        )

    return (
        resultados["aviso_robos_encerrados"],
        resultados["terminal_parar_robos"],
        resultados["fechar_terminal_parar_robos"],
    )


def _resolver_templates_fechamento_rdp():
    return (
        _resolver_template_padrao_ou_env_sem_validar(
            "GCV_FECHAR_RDP_NORMAL_IMAGE",
            DEFAULT_FECHAR_RDP_NORMAL_IMAGES,
        ),
        _resolver_template_padrao_ou_env_sem_validar(
            "GCV_FECHAR_RDP_HOVER_IMAGE",
            DEFAULT_FECHAR_RDP_HOVER_IMAGE,
        ),
        _resolver_template_padrao_ou_env_sem_validar(
            "GCV_CONFIRMACAO_DESCONEXAO_RDP_IMAGE",
            DEFAULT_CONFIRMACAO_DESCONEXAO_RDP_IMAGE,
        ),
        _resolver_template_padrao_ou_env_sem_validar(
            "GCV_OK_DESCONEXAO_RDP_IMAGE",
            DEFAULT_OK_DESCONEXAO_RDP_IMAGE,
        ),
    )


def _resolver_template_padrao_ou_env_sem_validar(env_name, default_path):
    raw = (os.getenv(env_name) or "").strip()
    if not raw:
        return _normalizar_template_paths(default_path)

    paths = []
    for parte in re.split(r"[;|]", raw):
        parte = parte.strip().strip('"')
        if parte:
            paths.append(_resolver_path(parte))

    return paths or [default_path]


def _diagnosticar_dependencias():
    ausentes = [
        dependencia
        for dependencia in GCV_DEPENDENCIES
        if importlib.util.find_spec(dependencia) is None
    ]

    return {
        "ok": not ausentes,
        "ausentes": ausentes,
        "mensagem": (
            "Dependencias GCV disponiveis."
            if not ausentes
            else "Dependencias ausentes: " + ", ".join(ausentes)
        ),
    }


def _diagnosticar_executavel():
    try:
        _resolver_executavel()
        return {"ok": True, "mensagem": "Executavel GCV encontrado."}
    except GcvAutomationError as exc:
        return {"ok": False, "mensagem": exc.message}
    except Exception as exc:
        return {"ok": False, "mensagem": f"Erro ao validar executavel GCV: {exc}"}


def _diagnosticar_senha():
    try:
        _obter_senha()
        return {"ok": True, "mensagem": "Senha GCV configurada."}
    except GcvAutomationError as exc:
        return {"ok": False, "mensagem": exc.message}
    except Exception as exc:
        return {"ok": False, "mensagem": f"Erro ao validar senha GCV: {exc}"}


def _diagnosticar_sessao_interativa():
    try:
        _validar_sessao_interativa()
        return {"ok": True, "mensagem": "Sessao interativa do Windows disponivel."}
    except GcvAutomationError as exc:
        return {"ok": False, "mensagem": exc.message}
    except Exception as exc:
        return {"ok": False, "mensagem": f"Erro ao validar sessao Windows: {exc}"}


def _resolver_executavel():
    configurado = (os.getenv("GCV_EXECUTABLE_PATH") or "").strip().strip('"')

    if configurado:
        caminho = _resolver_path(configurado)
        if not caminho.is_file():
            raise GcvAutomationError(
                f"Executavel GCV nao encontrado em '{caminho}'.",
                code="config",
            )
        return caminho

    area_trabalho = _obter_area_trabalho_windows()
    caminho = area_trabalho / "ROBO GCV" / "csrobogcv (1).exe"

    if caminho.is_file():
        return caminho

    raise GcvAutomationError(
        EXECUTABLE_NOT_FOUND_MESSAGE,
        code="executavel_nao_encontrado",
    )


class _GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", ctypes.c_ubyte * 8),
    ]

    def __init__(self, data1, data2, data3, data4):
        super().__init__()
        self.Data1 = data1
        self.Data2 = data2
        self.Data3 = data3
        self.Data4 = (ctypes.c_ubyte * 8)(*data4)


def _obter_area_trabalho_windows():
    if os.name != "nt":
        raise GcvAutomationError(
            "A automacao GCV precisa ser executada em um computador Windows.",
            code="config",
        )

    folderid_desktop = _GUID(
        0xB4BFCC3A,
        0xDB2C,
        0x424C,
        (0xB0, 0x29, 0x7F, 0xE9, 0x9A, 0x87, 0xC6, 0x41),
    )
    path_pointer = ctypes.c_void_p()
    shell32 = ctypes.windll.shell32
    ole32 = ctypes.windll.ole32

    shell32.SHGetKnownFolderPath.argtypes = [
        ctypes.POINTER(_GUID),
        wintypes.DWORD,
        wintypes.HANDLE,
        ctypes.POINTER(ctypes.c_void_p),
    ]
    shell32.SHGetKnownFolderPath.restype = ctypes.c_long
    ole32.CoTaskMemFree.argtypes = [ctypes.c_void_p]

    resultado = shell32.SHGetKnownFolderPath(
        ctypes.byref(folderid_desktop),
        0,
        None,
        ctypes.byref(path_pointer),
    )

    if resultado != 0 or not path_pointer.value:
        raise GcvAutomationError(
            "Nao foi possivel resolver a Area de Trabalho pelo Windows Known Folders.",
            code="config",
        )

    try:
        return Path(ctypes.wstring_at(path_pointer))
    finally:
        ole32.CoTaskMemFree(path_pointer)


def _validar_sessao_interativa():
    if os.name != "nt":
        return

    session_id = wintypes.DWORD()
    ok = ctypes.windll.kernel32.ProcessIdToSessionId(
        ctypes.windll.kernel32.GetCurrentProcessId(),
        ctypes.byref(session_id),
    )

    if ok and session_id.value == 0:
        raise GcvAutomationError(
            (
                "A automacao GCV precisa rodar na sessao interativa do Windows, "
                "nao como servico isolado na Session 0."
            ),
            code="sessao_windows",
        )


def _obter_senha():
    senha = os.getenv("GCV_ROBO_PASSWORD")
    if senha:
        return senha

    target = (
        os.getenv("GCV_ROBO_PASSWORD_CREDENTIAL_TARGET")
        or DEFAULT_CREDENTIAL_TARGET
    ).strip()
    senha = _ler_credencial_windows(target)

    if senha:
        return senha

    raise GcvAutomationError(
        (
            "Senha GCV nao configurada. Defina GCV_ROBO_PASSWORD no backend/.env "
            f"ou cadastre uma credencial generica do Windows com alvo '{target}'."
        ),
        code="config",
    )


def _ler_credencial_windows(target):
    if os.name != "nt" or not target:
        return None

    class FILETIME(ctypes.Structure):
        _fields_ = [
            ("dwLowDateTime", ctypes.c_ulong),
            ("dwHighDateTime", ctypes.c_ulong),
        ]

    class CREDENTIALW(ctypes.Structure):
        _fields_ = [
            ("Flags", ctypes.c_ulong),
            ("Type", ctypes.c_ulong),
            ("TargetName", ctypes.c_wchar_p),
            ("Comment", ctypes.c_wchar_p),
            ("LastWritten", FILETIME),
            ("CredentialBlobSize", ctypes.c_ulong),
            ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)),
            ("Persist", ctypes.c_ulong),
            ("AttributeCount", ctypes.c_ulong),
            ("Attributes", ctypes.c_void_p),
            ("TargetAlias", ctypes.c_wchar_p),
            ("UserName", ctypes.c_wchar_p),
        ]

    credential_pointer = ctypes.POINTER(CREDENTIALW)()
    advapi32 = ctypes.windll.advapi32
    advapi32.CredReadW.argtypes = [
        ctypes.c_wchar_p,
        ctypes.c_ulong,
        ctypes.c_ulong,
        ctypes.POINTER(ctypes.POINTER(CREDENTIALW)),
    ]
    advapi32.CredReadW.restype = ctypes.c_bool
    advapi32.CredFree.argtypes = [ctypes.c_void_p]

    CRED_TYPE_GENERIC = 1
    ok = advapi32.CredReadW(
        target,
        CRED_TYPE_GENERIC,
        0,
        ctypes.byref(credential_pointer),
    )

    if not ok:
        return None

    try:
        credential = credential_pointer.contents
        blob = ctypes.string_at(
            credential.CredentialBlob,
            credential.CredentialBlobSize,
        )

        for encoding in ("utf-16-le", "utf-8", "mbcs"):
            try:
                valor = blob.decode(encoding).rstrip("\x00")
            except UnicodeDecodeError:
                continue

            if valor:
                return valor
    finally:
        advapi32.CredFree(credential_pointer)

    return None


def _resolver_template_padrao_ou_env(rotulo, env_name, default_path):
    raw = (os.getenv(env_name) or "").strip()

    if raw:
        return _resolver_paths_imagens(env_name, obrigatorio=True, rotulo=rotulo)

    paths = _normalizar_template_paths(default_path)
    ausentes = [path for path in paths if not path.is_file()]
    if ausentes:
        detalhes = ", ".join(_caminho_para_log(path) for path in ausentes)
        raise GcvAutomationError(
            f"Template {rotulo} ausente: '{detalhes}'.",
            code="template_ausente",
        )

    return paths


def _normalizar_template_paths(default_path):
    if isinstance(default_path, (list, tuple)):
        return list(default_path)

    return [default_path]


def _resolver_paths_imagens(env_name, obrigatorio, rotulo=None):
    raw = (os.getenv(env_name) or "").strip()
    paths = []

    for parte in re.split(r"[;|]", raw):
        parte = parte.strip().strip('"')
        if not parte:
            continue
        caminho = _resolver_path(parte)
        if not caminho.is_file():
            if rotulo:
                raise GcvAutomationError(
                    f"Template {rotulo} ausente: '{_caminho_para_log(caminho)}'.",
                    code="template_ausente",
                )
            raise GcvAutomationError(
                f"Imagem configurada em {env_name} nao encontrada: '{caminho}'.",
                code="config",
            )
        paths.append(caminho)

    if obrigatorio and not paths:
        if rotulo:
            raise GcvAutomationError(
                f"Template {rotulo} ausente: nenhuma imagem configurada em {env_name}.",
                code="template_ausente",
            )
        raise GcvAutomationError(
            f"Configure {env_name} com o caminho do template de imagem.",
            code="config",
        )

    return paths


def _resolver_path(valor):
    caminho = Path(os.path.expandvars(os.path.expanduser(valor)))
    if caminho.is_absolute():
        return caminho
    return (REPO_ROOT / caminho).resolve()


def _caminho_para_log(caminho):
    try:
        return str(caminho.resolve().relative_to(REPO_ROOT))
    except Exception:
        return str(caminho)


def _abrir_executavel(exe_path):
    _log(f"Abrindo executavel GCV: {exe_path}")
    subprocess.Popen([str(exe_path)], cwd=str(exe_path.parent))


def _obter_janela_ativa_hwnd():
    if os.name != "nt":
        return None

    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
    except Exception:
        return None

    return int(hwnd) if hwnd else None


def _restaurar_janela_anterior(hwnd):
    if os.name != "nt" or not hwnd:
        return

    try:
        user32 = ctypes.windll.user32
        if not user32.IsWindow(hwnd):
            return

        if user32.IsIconic(hwnd):
            user32.ShowWindow(hwnd, SW_RESTORE)
        else:
            user32.ShowWindow(hwnd, SW_SHOW)

        user32.SetForegroundWindow(hwnd)
        _log("Janela ativa anterior restaurada.")
    except Exception as exc:
        _log(f"Nao foi possivel restaurar a janela ativa anterior: {exc}")


def _manter_rdp_visivel_para_recuperacao(rdp_window):
    if rdp_window is None:
        return

    try:
        _preparar_rdp_por_hwnd(rdp_window)
        _log("RDP deixada visivel para recuperacao manual.")
    except Exception as exc:
        _log(f"Nao foi possivel tentar restaurar a RDP para recuperacao: {exc}")


def _preparar_janela_remota(janela):
    return _preparar_janela_para_interacao(
        janela,
        "Area de Trabalho Remota",
        maximizar=True,
    )


def _preparar_janela_para_interacao(janela, descricao, maximizar=False, erro_foco=None):
    hwnd = _hwnd_da_janela(janela)
    if not hwnd:
        raise GcvAutomationError(
            f"Nao foi possivel obter o identificador da janela: {descricao}.",
            code="foco_janela",
            screenshot=True,
        )

    try:
        if os.name == "nt":
            user32 = ctypes.windll.user32
            if not user32.IsWindow(hwnd):
                raise RuntimeError("Handle de janela invalido.")

            if user32.IsIconic(hwnd):
                user32.ShowWindow(hwnd, SW_RESTORE)
                time.sleep(0.4)
            else:
                user32.ShowWindow(hwnd, SW_SHOW)

        try:
            if maximizar:
                janela.maximize()
        except Exception as exc:
            _log(f"Nao foi possivel maximizar por pywinauto ({descricao}): {exc}")
            if os.name == "nt":
                try:
                    ctypes.windll.user32.ShowWindow(hwnd, SW_MAXIMIZE)
                except Exception as fallback_exc:
                    _log(
                        f"Nao foi possivel maximizar por WinAPI ({descricao}): "
                        f"{fallback_exc}"
                    )

        try:
            janela.set_focus()
        except Exception as exc:
            _log(f"Tentativa de foco por pywinauto falhou ({descricao}): {exc}")

        if os.name == "nt":
            try:
                ctypes.windll.user32.SetForegroundWindow(hwnd)
            except Exception as exc:
                _log(f"Tentativa de foreground falhou ({descricao}): {exc}")

        _log(f"Tentativa de restaurar/maximizar concluida: {descricao}")
        return hwnd
    except Exception as exc:
        raise GcvAutomationError(
            erro_foco or f"Nao foi possivel preparar a janela: {descricao}.",
            code="foco_janela",
            screenshot=True,
        ) from exc


def _hwnd_da_janela(janela):
    try:
        return int(janela.handle)
    except Exception:
        return None


def _desktop():
    try:
        from pywinauto import Desktop
    except ImportError as exc:
        raise GcvAutomationError(
            "Dependencia pywinauto nao instalada. Rode pip install -r backend/requirements.txt.",
            code="config",
        ) from exc

    return Desktop(backend="uia")


def _pyautogui():
    try:
        import pyautogui
    except ImportError as exc:
        raise GcvAutomationError(
            "Dependencia pyautogui nao instalada. Rode pip install -r backend/requirements.txt.",
            code="config",
        ) from exc

    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0.05
    return pyautogui


def _aguardar_janela_por_titulo(pattern, timeout_s, descricao, obrigatoria=True):
    deadline = time.monotonic() + timeout_s

    while time.monotonic() < deadline:
        janela = _primeira_janela_por_titulo(pattern)
        if janela:
            _focar_janela(janela)
            _log(f"Janela localizada: {descricao}")
            return janela
        time.sleep(POLL_INTERVAL_S)

    if obrigatoria:
        raise GcvAutomationError(
            f"Nao localizei {descricao} dentro do timeout de {timeout_s}s.",
            code="timeout",
            screenshot=True,
        )

    _log(f"Janela opcional nao localizada: {descricao}")
    return None


def _primeira_janela_por_titulo(pattern):
    regex = re.compile(pattern, re.IGNORECASE)

    for janela in _desktop().windows(visible_only=False):
        try:
            titulo = (janela.window_text() or "").strip()
        except Exception:
            continue

        if titulo and regex.search(titulo):
            return janela

    return None


def _validar_texto_janela(janela, texto_esperado):
    deadline = time.monotonic() + 10

    while time.monotonic() < deadline:
        if _janela_contem_texto(janela, texto_esperado):
            _log("Texto da janela de senha confirmado.")
            return
        time.sleep(0.5)

    raise GcvAutomationError(
        "A janela de senha apareceu, mas o texto esperado nao foi localizado.",
        code="login_inesperado",
        screenshot=True,
    )


def _janela_contem_texto(janela, texto_esperado):
    esperado = texto_esperado.strip().lower()
    textos = []

    try:
        textos.append(janela.window_text() or "")
    except Exception:
        pass

    try:
        for controle in janela.descendants():
            try:
                textos.append(controle.window_text() or "")
            except Exception:
                continue
    except Exception:
        pass

    texto_total = " ".join(textos).lower()
    return esperado in texto_total


def _preencher_senha(login_window, password):
    campo = _primeiro_campo_senha(login_window)
    _focar_janela(login_window)

    try:
        campo.set_focus()
    except Exception:
        pass

    try:
        campo.click_input()
    except Exception:
        pass

    try:
        campo.set_edit_text(password)
    except Exception:
        try:
            campo.set_text(password)
        except Exception as exc:
            raise GcvAutomationError(
                "Nao foi possivel preencher o campo de senha.",
                code="login_senha",
                screenshot=True,
            ) from exc

    try:
        from pywinauto.keyboard import send_keys
    except ImportError as exc:
        raise GcvAutomationError(
            "Dependencia pywinauto nao instalada para enviar ENTER.",
            code="config",
        ) from exc

    send_keys("{ENTER}")
    _log("Senha enviada para a janela Password.")


def _primeiro_campo_senha(login_window):
    try:
        campos = login_window.descendants(control_type="Edit")
    except Exception:
        campos = []

    for campo in campos:
        try:
            if campo.is_enabled():
                return campo
        except Exception:
            continue

    raise GcvAutomationError(
        "Campo de senha nao localizado na janela Password.",
        code="login_senha",
        screenshot=True,
    )


def _aguardar_area_trabalho_pronta(rdp_window, config, timeout_s=None):
    timeout_s = DESKTOP_TIMEOUT_S if timeout_s is None else timeout_s
    deadline = time.monotonic() + timeout_s
    hwnd = _obter_hwnd_rdp(rdp_window)
    _log_retangulo_rdp(hwnd)

    while time.monotonic() < deadline:
        screenshot, origem = _screenshot_janela_por_hwnd(hwnd)
        parar_match = _localizar_imagem(
            screenshot,
            origem,
            config.parar_icon_images,
        )

        if parar_match:
            _log_match_localizado("Parar Robos apos login", parar_match)
            _log("Area de Trabalho Remota pronta: Parar Robos localizado.")
            return parar_match, None

        time.sleep(POLL_INTERVAL_S)

    raise GcvAutomationError(
        PARAR_NOT_FOUND_AFTER_LOGIN_MESSAGE,
        code="parar_nao_localizado_pos_login",
        screenshot=True,
    )


def _aguardar_icone_monitorar(rdp_window, config, timeout_s):
    deadline = time.monotonic() + timeout_s
    hwnd = _obter_hwnd_rdp(rdp_window)
    _log_retangulo_rdp(hwnd)

    while time.monotonic() < deadline:
        screenshot, origem = _screenshot_janela_por_hwnd(hwnd)
        monitorar_match = _localizar_imagem(
            screenshot,
            origem,
            config.monitorar_icon_images,
        )

        if monitorar_match:
            _log_match_localizado("Monitorar Robos", monitorar_match)
            return monitorar_match

        time.sleep(POLL_INTERVAL_S)

    raise GcvAutomationError(
        _mensagem_template_nao_localizado(
            "monitorar_robos.png",
            config.monitorar_icon_images,
        ),
        code="monitorar_nao_localizado",
        screenshot=True,
    )


def _fechar_template_na_rdp(rdp_window, imagens, descricao, x_ratio, y_ratio):
    match = _aguardar_template_na_rdp(
        rdp_window,
        imagens,
        STOP_VISUAL_TIMEOUT_S,
        descricao,
    )
    x = int(round(match.left + match.width * x_ratio))
    y = int(round(match.top + match.height * y_ratio))
    _log(
        f"Coordenada calculada para o X do {descricao}: "
        f"x={x}, y={y}, proporcao=({x_ratio:.4f},{y_ratio:.4f}), "
        f"{_formatar_match(match)}."
    )
    _pyautogui().click(x=x, y=y)
    _log(f"Clique no X do {descricao} executado.")


def _fechar_terminal_parar_robos_na_rdp(rdp_window, config):
    terminal_match = _aguardar_template_na_rdp(
        rdp_window,
        config.terminal_parar_robos_images,
        STOP_VISUAL_TIMEOUT_S,
        "terminal Parar Robôs",
    )
    pyautogui = _pyautogui()

    for tentativa in (1, 2):
        _log("Procurando botão X do terminal Parar Robôs.")
        x_match = _aguardar_botao_x_terminal_parar_robos(
            rdp_window,
            terminal_match,
            config.fechar_terminal_parar_robos_images,
            STOP_VISUAL_TIMEOUT_S,
        )
        _log(
            "Botão X do terminal Parar Robôs localizado: "
            f"{_formatar_match(x_match)}."
        )
        x, y = x_match.center
        _log(f"Movendo mouse para o X do terminal: x={x}, y={y}.")
        pyautogui.moveTo(x=x, y=y)
        time.sleep(0.4)
        _log(f"Tentativa {tentativa} de fechar terminal Parar Robôs.")
        pyautogui.click(x=x, y=y)
        time.sleep(2)

        terminal_match = _template_visivel_na_rdp(
            rdp_window,
            config.terminal_parar_robos_images,
        )
        if not terminal_match:
            _log("Template desapareceu da RDP: terminal Parar Robôs.")
            return

        if tentativa == 1:
            _log("Terminal ainda visível após tentativa 1; tentando novamente.")

    raise GcvAutomationError(
        "Nao foi possivel confirmar o fechamento de terminal Parar Robôs.",
        code="template_nao_fechou",
        screenshot=True,
    )


def _aguardar_botao_x_terminal_parar_robos(
    rdp_window,
    terminal_match,
    imagens,
    timeout_s,
):
    deadline = time.monotonic() + timeout_s
    hwnd = _obter_hwnd_rdp(rdp_window)
    left, top, width, height = _regiao_busca_x_terminal_parar_robos(
        hwnd,
        terminal_match,
    )
    _log(
        "Região de busca do X do terminal Parar Robôs: "
        f"left={left}, top={top}, width={width}, height={height}."
    )

    while time.monotonic() < deadline:
        screenshot = _pyautogui().screenshot(region=(left, top, width, height))
        match = _localizar_imagem(screenshot, (left, top), imagens)
        if match:
            _log_match_localizado("botão X do terminal Parar Robôs", match)
            return match
        time.sleep(VISUAL_POLL_INTERVAL_S)

    raise GcvAutomationError(
        _mensagem_template_nao_localizado(
            "botão X do terminal Parar Robôs",
            imagens,
        ),
        code="x_terminal_nao_localizado",
        screenshot=True,
    )


def _regiao_busca_x_terminal_parar_robos(hwnd, terminal_match):
    rdp_left, rdp_top, rdp_width, rdp_height = _retangulo_hwnd(hwnd)
    return _calcular_regiao_busca_x_terminal_parar_robos(
        terminal_match,
        rdp_left,
        rdp_top,
        rdp_width,
        rdp_height,
    )


def _calcular_regiao_busca_x_terminal_parar_robos(
    terminal_match,
    rdp_left,
    rdp_top,
    rdp_width,
    rdp_height,
):
    rdp_right = rdp_left + rdp_width
    rdp_bottom = rdp_top + rdp_height
    search_width = max(
        80,
        min(terminal_match.width, int(round(terminal_match.width * 0.24))),
    )
    search_height = max(
        terminal_match.height,
        int(round(terminal_match.height * 1.5)),
    )

    left = max(rdp_left, terminal_match.right - search_width)
    top = max(rdp_top, terminal_match.top)
    right = min(rdp_right, terminal_match.right)
    bottom = min(rdp_bottom, terminal_match.top + search_height)

    if right <= left or bottom <= top:
        raise GcvAutomationError(
            "Nao foi possivel calcular a regiao de busca do X do terminal Parar Robôs.",
            code="x_terminal_regiao",
            screenshot=True,
        )

    return int(left), int(top), int(right - left), int(bottom - top)


def _aguardar_template_na_rdp(rdp_window, imagens, timeout_s, descricao):
    deadline = time.monotonic() + timeout_s
    hwnd = _obter_hwnd_rdp(rdp_window)
    _log_retangulo_rdp(hwnd)

    while time.monotonic() < deadline:
        screenshot, origem = _screenshot_janela_por_hwnd(hwnd)
        match = _localizar_imagem(screenshot, origem, imagens)
        if match:
            _log_match_localizado(descricao, match)
            return match
        time.sleep(VISUAL_POLL_INTERVAL_S)

    raise GcvAutomationError(
        _mensagem_template_nao_localizado(descricao, imagens),
        code="template_nao_localizado",
        screenshot=True,
    )


def _confirmar_template_sumiu_na_rdp(rdp_window, imagens, descricao):
    if _template_visivel_na_rdp(rdp_window, imagens):
        raise GcvAutomationError(
            f"Nao foi possivel confirmar o fechamento de {descricao}.",
            code="template_nao_fechou",
            screenshot=True,
        )
    _log(f"Template desapareceu da RDP: {descricao}.")


def _template_visivel_na_rdp(rdp_window, imagens):
    hwnd = _obter_hwnd_rdp(rdp_window)
    screenshot, origem = _screenshot_janela_por_hwnd(hwnd)
    return _localizar_imagem(screenshot, origem, imagens)


def _formatar_match(match):
    partes = [
        f"posicao=({match.left},{match.top})",
        f"tamanho=({match.width}x{match.height})",
    ]

    if match.scale is not None:
        partes.append(f"escala={match.scale:.3f}")
    if match.template_name is not None:
        partes.append(f"template={match.template_name}")
    if match.confidence is not None:
        partes.append(f"confianca={match.confidence:.3f}")
    if match.mean_diff is not None:
        partes.append(f"diferenca_media={match.mean_diff:.2f}")

    return ", ".join(partes)


def _log_match_localizado(descricao, match):
    _log(f"Template localizado: {descricao}: {_formatar_match(match)}.")


def _log_retangulo_rdp(hwnd):
    left, top, width, height = _retangulo_hwnd(hwnd)
    _log(
        "Retangulo RDP: "
        f"left={left}, top={top}, width={width}, height={height}."
    )


def _preparar_rdp_por_hwnd(rdp_window):
    hwnd = _obter_hwnd_rdp(rdp_window)

    if os.name == "nt":
        user32 = ctypes.windll.user32
        try:
            if user32.IsIconic(hwnd):
                user32.ShowWindow(hwnd, SW_RESTORE)
            else:
                user32.ShowWindow(hwnd, SW_SHOW)
        except Exception as exc:
            _log(f"Tentativa de restaurar RDP falhou: {exc}")

        try:
            user32.ShowWindow(hwnd, SW_MAXIMIZE)
        except Exception as exc:
            _log(f"Tentativa de maximizar RDP falhou: {exc}")

        try:
            user32.SetForegroundWindow(hwnd)
        except Exception as exc:
            _log(f"Tentativa de foreground da RDP falhou: {exc}")

    _log("Tentativa de restaurar/maximizar RDP concluida.")
    return hwnd


def _fechar_rdp_visualmente(hwnd, config):
    _log("Revelando barra superior da RDP.")
    pyautogui = _pyautogui()
    screen_width, _ = pyautogui.size()
    pyautogui.moveTo(x=screen_width // 2, y=1)
    time.sleep(RDP_REVEAL_BAR_DELAY_S)

    _log("Procurando botão X da RDP.")
    x_match = _localizar_botao_x_rdp(config)
    if not x_match:
        return RdpCloseResult(
            fechada=False,
            mensagem=SUCCESS_RDP_X_NOT_FOUND_MESSAGE,
            codigo="ok_rdp_x_nao_localizado",
            screenshot_path=_capturar_print("rdp_x_nao_localizado"),
            manter_rdp_visivel=True,
        )

    _log(
        "Botão X localizado: "
        f"template={x_match.template_name}, escala={x_match.scale:.3f}, "
        f"confiança={x_match.confidence:.3f}"
    )
    pyautogui.click(*x_match.center)
    _log("Clique no X da RDP.")

    _log("Aguardando confirmação de desconexão.")
    confirmacao_match = _aguardar_confirmacao_desconexao_rdp(config)
    if not confirmacao_match:
        return RdpCloseResult(
            fechada=False,
            mensagem=SUCCESS_RDP_CONFIRM_FAILED_MESSAGE,
            codigo="ok_rdp_confirmacao_nao_localizada",
            screenshot_path=_capturar_print("rdp_confirmacao_nao_localizada"),
            manter_rdp_visivel=True,
        )

    _log("Confirmação de desconexão localizada.")
    ok_match = _localizar_ok_desconexao_rdp(config, confirmacao_match)
    if not ok_match:
        return RdpCloseResult(
            fechada=False,
            mensagem=SUCCESS_RDP_CONFIRM_FAILED_MESSAGE,
            codigo="ok_rdp_ok_nao_localizado",
            screenshot_path=_capturar_print("rdp_ok_nao_localizado"),
            manter_rdp_visivel=True,
        )

    _log(
        "Botão OK localizado: "
        f"escala={ok_match.scale:.3f}, confiança={ok_match.confidence:.3f}"
    )
    pyautogui.click(*ok_match.center)
    _log("Clique no OK da desconexão.")

    if _aguardar_hwnd_desaparecer(hwnd, RDP_CLOSE_VERIFY_TIMEOUT_S):
        _log("Cliente RDP encerrado com sucesso.")
        return RdpCloseResult(
            fechada=True,
            mensagem=SUCCESS_MESSAGE,
            codigo="ok",
        )

    return RdpCloseResult(
        fechada=False,
        mensagem=SUCCESS_RDP_CONFIRM_FAILED_MESSAGE,
        codigo="ok_rdp_nao_desapareceu",
        screenshot_path=_capturar_print("rdp_nao_desapareceu"),
        manter_rdp_visivel=True,
    )


def _localizar_botao_x_rdp(config):
    screenshot, origem = _screenshot_faixa_superior_tela()
    for imagens in (
        config.fechar_rdp_normal_images,
        config.fechar_rdp_hover_images,
    ):
        match = _localizar_imagem(screenshot, origem, imagens)
        if match:
            return match

    return None


def _aguardar_confirmacao_desconexao_rdp(config):
    deadline = time.monotonic() + RDP_CONFIRMATION_TIMEOUT_S

    while time.monotonic() < deadline:
        screenshot, origem = _screenshot_tela_inteira()
        match = _localizar_imagem(
            screenshot,
            origem,
            config.confirmacao_desconexao_rdp_images,
        )
        if match:
            _log_match_localizado("confirmacao desconexao RDP", match)
            return match

        time.sleep(VISUAL_POLL_INTERVAL_S)

    return None


def _localizar_ok_desconexao_rdp(config, confirmacao_match):
    screenshot, origem = _screenshot_template_region(confirmacao_match)
    match = _localizar_imagem(
        screenshot,
        origem,
        config.ok_desconexao_rdp_images,
    )
    if match:
        _log_match_localizado("OK desconexao RDP", match)
    return match


def _screenshot_faixa_superior_tela():
    pyautogui = _pyautogui()
    screen_width, screen_height = pyautogui.size()
    height = max(1, min(int(RDP_TOP_BAR_SEARCH_HEIGHT), int(screen_height)))
    screenshot = pyautogui.screenshot(region=(0, 0, int(screen_width), height))
    return screenshot, (0, 0)


def _screenshot_tela_inteira():
    return _pyautogui().screenshot(), (0, 0)


def _screenshot_template_region(match):
    pyautogui = _pyautogui()
    screen_width, screen_height = pyautogui.size()
    left = max(0, int(match.left))
    top = max(0, int(match.top))
    right = min(int(screen_width), int(match.right))
    bottom = min(int(screen_height), int(match.bottom))

    if right <= left or bottom <= top:
        return pyautogui.screenshot(region=(0, 0, 1, 1)), (0, 0)

    screenshot = pyautogui.screenshot(region=(left, top, right - left, bottom - top))
    return screenshot, (left, top)


def _aguardar_hwnd_desaparecer(hwnd, timeout_s):
    deadline = time.monotonic() + timeout_s

    while time.monotonic() < deadline:
        if not _hwnd_existe(hwnd):
            return True
        time.sleep(0.3)

    return not _hwnd_existe(hwnd)


def _hwnd_existe(hwnd):
    if os.name != "nt" or not hwnd:
        return False

    try:
        return bool(ctypes.windll.user32.IsWindow(int(hwnd)))
    except Exception:
        return False


def _obter_hwnd_rdp(rdp_window):
    hwnd = _hwnd_da_janela(rdp_window)
    if not hwnd:
        raise GcvAutomationError(
            "Nao foi possivel obter o identificador da Area de Trabalho Remota.",
            code="foco_janela",
            screenshot=True,
        )

    if os.name == "nt" and not ctypes.windll.user32.IsWindow(hwnd):
        raise GcvAutomationError(
            "A janela da Area de Trabalho Remota nao esta mais disponivel.",
            code="foco_janela",
            screenshot=True,
        )

    return hwnd


def _retangulo_hwnd(hwnd):
    if os.name != "nt":
        raise GcvAutomationError(
            "A automacao GCV precisa ser executada em um computador Windows.",
            code="config",
        )

    rect = wintypes.RECT()
    ok = ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
    if not ok:
        raise GcvAutomationError(
            "Nao foi possivel obter o retangulo da Area de Trabalho Remota.",
            code="foco_janela",
            screenshot=True,
        )

    return _limitar_retangulo_a_tela(
        int(rect.left),
        int(rect.top),
        int(rect.right),
        int(rect.bottom),
    )


def _screenshot_janela_por_hwnd(hwnd):
    left, top, width, height = _retangulo_hwnd(hwnd)
    screenshot = _pyautogui().screenshot(region=(left, top, width, height))
    return screenshot, (left, top)


def _screenshot_janela(janela):
    pyautogui = _pyautogui()
    _focar_janela(janela)
    rect = janela.rectangle()
    left, top, width, height = _limitar_retangulo_a_tela(
        int(rect.left),
        int(rect.top),
        int(rect.right),
        int(rect.bottom),
    )
    screenshot = pyautogui.screenshot(region=(left, top, width, height))
    return screenshot, (left, top)


def _limitar_retangulo_a_tela(left, top, right, bottom):
    screen_width, screen_height = _pyautogui().size()
    left = max(0, int(left))
    top = max(0, int(top))
    right = min(int(screen_width), int(right))
    bottom = min(int(screen_height), int(bottom))

    if right <= left or bottom <= top:
        raise GcvAutomationError(
            "O retangulo da Area de Trabalho Remota ficou fora da tela fisica.",
            code="retangulo_rdp",
            screenshot=True,
        )

    return left, top, right - left, bottom - top


def _localizar_imagem(screenshot, origem, imagens):
    return _localizar_imagem_opencv(screenshot, origem, imagens)


def _localizar_imagem_opencv(screenshot, origem, imagens):
    try:
        import cv2
        import numpy as np
    except ImportError:
        return None

    origem_x, origem_y = origem
    haystack = np.array(screenshot.convert("RGB"))
    haystack_height, haystack_width = haystack.shape[:2]
    best_match = None
    best_score = 0.0

    for imagem in imagens:
        template_base = cv2.imread(str(imagem), cv2.IMREAD_COLOR)
        if template_base is None:
            continue
        template_base = cv2.cvtColor(template_base, cv2.COLOR_BGR2RGB)

        for escala in _variacoes_escala_imagem(haystack_width, haystack_height):
            template = template_base
            if abs(escala - 1.0) > 0.001:
                width = int(round(template_base.shape[1] * escala))
                height = int(round(template_base.shape[0] * escala))
                if width < 8 or height < 8:
                    continue
                interpolation = cv2.INTER_AREA if escala < 1.0 else cv2.INTER_CUBIC
                template = cv2.resize(
                    template_base,
                    (width, height),
                    interpolation=interpolation,
                )

            template_height, template_width = template.shape[:2]
            if (
                template_width > haystack_width
                or template_height > haystack_height
            ):
                continue

            result = cv2.matchTemplate(haystack, template, cv2.TM_CCOEFF_NORMED)
            _, score, _, location = cv2.minMaxLoc(result)
            candidate = haystack[
                int(location[1]) : int(location[1]) + template_height,
                int(location[0]) : int(location[0]) + template_width,
            ]
            mean_diff = float(
                np.mean(cv2.absdiff(candidate.astype("uint8"), template.astype("uint8")))
            )
            if mean_diff > IMAGE_MAX_MEAN_DIFF:
                continue

            if score > best_score:
                best_score = score
                best_match = ImageMatch(
                    left=origem_x + int(location[0]),
                    top=origem_y + int(location[1]),
                    width=int(template_width),
                    height=int(template_height),
                    confidence=float(score),
                    mean_diff=mean_diff,
                    scale=float(escala),
                    template_name=imagem.name,
                )

    if best_match and best_score >= IMAGE_CONFIDENCE:
        return best_match

    return None


def _variacoes_escala_imagem(haystack_width=None, haystack_height=None):
    escala_min = min(IMAGE_SCALE_MIN, IMAGE_SCALE_MAX)
    escala_max = max(IMAGE_SCALE_MIN, IMAGE_SCALE_MAX)
    step = IMAGE_SCALE_STEP if IMAGE_SCALE_STEP > 0 else 0.05
    escala_estimada = _escala_estimada_rdp(haystack_width, haystack_height)
    escalas = []

    def adicionar(escala):
        if escala < escala_min or escala > escala_max:
            return
        escala = round(float(escala), 3)
        if not any(abs(escala - existente) <= 0.001 for existente in escalas):
            escalas.append(escala)

    adicionar(escala_estimada)
    adicionar(1.0)

    for parte in re.split(r"[,;| ]+", IMAGE_SCALE_VARIATIONS):
        parte = parte.strip()
        if not parte:
            continue

        try:
            escala = float(parte)
        except ValueError:
            continue

        if escala <= 0:
            continue

        adicionar(escala)

    total_steps = int(round((escala_max - escala_min) / step))
    for indice in range(total_steps + 1):
        adicionar(escala_min + indice * step)
    adicionar(escala_max)

    escalas.sort(
        key=lambda valor: (
            abs(valor - escala_estimada),
            abs(valor - 1.0),
            valor,
        )
    )

    return escalas


def _escala_estimada_rdp(haystack_width, haystack_height):
    if (
        not haystack_width
        or not haystack_height
        or IMAGE_BASE_RDP_WIDTH <= 0
        or IMAGE_BASE_RDP_HEIGHT <= 0
    ):
        return 1.0

    estimada = min(
        float(haystack_width) / IMAGE_BASE_RDP_WIDTH,
        float(haystack_height) / IMAGE_BASE_RDP_HEIGHT,
    )
    escala_min = min(IMAGE_SCALE_MIN, IMAGE_SCALE_MAX)
    escala_max = max(IMAGE_SCALE_MIN, IMAGE_SCALE_MAX)
    return max(min(estimada, escala_max), escala_min)


def _duplo_clique(rdp_window, match, descricao):
    pyautogui = _pyautogui()
    x, y = match.center
    _log(f"Duplo clique em {descricao}.")
    pyautogui.doubleClick(x=x, y=y, interval=0.15)


def _clicar(rdp_window, match, descricao):
    pyautogui = _pyautogui()
    x, y = match.center
    _log(f"Clique em {descricao}.")
    pyautogui.click(x=x, y=y)


def _capturar_print(prefixo):
    try:
        ensure_runtime_dirs()
        pyautogui = _pyautogui()
        nome = f"{prefixo}_{time.strftime('%Y%m%d_%H%M%S')}.png"
        caminho = GCV_PRINTS_DIR / nome
        pyautogui.screenshot().save(caminho)
        _log(f"Print salvo em {caminho}")
        return str(caminho)
    except Exception as exc:
        _log(f"Falha ao capturar print: {exc}")
        return None


def _focar_janela(janela):
    try:
        if janela.is_minimized():
            janela.restore()
    except Exception:
        pass

    try:
        janela.set_focus()
    except Exception:
        pass


def _enviar_andamento(notificar, mensagem):
    _log(mensagem)
    if notificar is None:
        return

    try:
        notificar(mensagem)
    except Exception as exc:
        _log(f"Falha ao enviar andamento ao Telegram: {exc}")


def _log(mensagem):
    print(f"[GCV] {mensagem}")
