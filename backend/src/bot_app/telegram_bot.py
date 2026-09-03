import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update
from telegram.helpers import escape_markdown
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from bot_app.automations.bluepex import liberar_visitante
from bot_app.automations.consultor_cs import liberar_consultor
from bot_app.automations.gcv_robos import (
    diagnosticar_gcv,
    reiniciar_robos_gcv,
)
from bot_app.common.paths import ENV_PATH
from bot_app.services.history_store import init_history_store
from bot_app.services.job_queue import (
    init_job_queue,
    submit_job,
    submit_job_once,
    wait_for_job,
)

load_dotenv(dotenv_path=ENV_PATH, override=True)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GCV_ALLOWED_CHAT_IDS = os.getenv("GCV_ALLOWED_CHAT_IDS", "")

# =========================
# CORES TERMINAL
# =========================
RESET = "\033[0m"
VERDE = "\033[92m"
VERMELHO = "\033[91m"
AMARELO = "\033[93m"
AZUL = "\033[94m"
CIANO = "\033[96m"
NEGRITO = "\033[1m"


def md(value):
    return escape_markdown("" if value is None else str(value), version=1)


def parse_chat_ids(raw: str):
    ids = set()

    for parte in raw.split(","):
        parte = parte.strip()
        if not parte:
            continue
        try:
            ids.add(int(parte))
        except ValueError:
            print(f"{AMARELO}[AVISO]{RESET} Chat ID GCV invalido ignorado: {parte}")

    return ids


def chat_autorizado_gcv(chat):
    if not GCV_ALLOWED_CHAT_IDS.strip():
        print(
            f"{VERMELHO}[ERRO]{RESET} GCV_ALLOWED_CHAT_IDS nao configurado no backend/.env. "
            "Comandos GCV bloqueados."
        )
        return False

    chats_permitidos = parse_chat_ids(GCV_ALLOWED_CHAT_IDS)
    if not chats_permitidos:
        print(
            f"{VERMELHO}[ERRO]{RESET} GCV_ALLOWED_CHAT_IDS nao possui nenhum Chat ID valido. "
            "Comandos GCV bloqueados."
        )
        return False

    if not chat or chat.type not in {"group", "supergroup"}:
        return False

    return chat.id in chats_permitidos


async def enviar_print_telegram(update: Update, caminho):
    if not update.message or not caminho:
        return

    path = Path(str(caminho))
    if not path.is_file():
        return

    with path.open("rb") as imagem:
        await update.message.reply_photo(photo=imagem)


def criar_notificador_telegram(update: Update, loop):
    def notificar(mensagem):
        if not update.message:
            return

        future = asyncio.run_coroutine_threadsafe(
            update.message.reply_text(mensagem),
            loop,
        )
        future.result(timeout=15)

    return notificar


def extrair_nome_mac(texto: str):
    bruto = texto.replace("/liberar", "", 1).strip()
    bruto = bruto.replace("\n", " ").replace("\r", " ")

    if "|" not in bruto:
        raise ValueError(
            "Formato invalido.\n\n"
            "Use corretamente:\n"
            "/liberar Nome do Visitante | AA:BB:CC:DD:EE:FF"
        )

    nome, mac = bruto.split("|", 1)

    nome = nome.strip()
    mac = mac.strip()

    if not nome:
        raise ValueError("Nome do visitante nao informado.")
    if not mac:
        raise ValueError("Endereco MAC nao informado.")

    return nome, mac


def extrair_nome_data(texto: str):
    bruto = texto.replace("/consultor", "", 1).strip()

    if "|" not in bruto:
        raise ValueError("Formato invalido. Use: /consultor Nome | DD/MM/AAAA")

    nome, data = bruto.split("|", 1)

    nome = nome.strip()
    data = data.strip()

    if not nome:
        raise ValueError("Nome nao informado.")

    if not data:
        raise ValueError("Data nao informada.")

    return nome, data


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    await update.message.reply_text(
        "🤖 *BOT ONLINE*\n\n"
        "Sistema de automacoes ativo.\n\n"
        "*COMANDOS DISPONIVEIS:*\n\n"
        "1. 🧾 Liberar visitante no BluePex\n"
        "`/liberar Nome do Visitante | AA:BB:CC:DD:EE:FF`\n\n"
        "Exemplo:\n"
        "`/liberar Joao Silva | 00:11:22:33:44:55`\n\n"
        "2. ✅ Liberar consultor no CS\n"
        "`/consultor NOME_DO_CONSULTOR | DD/MM/AAAA`\n\n"
        "Exemplo:\n"
        "`/consultor CSCELSO | 28/04/2026`\n\n"
        "3. Reiniciar robos GCV\n"
        "`/reiniciar_gcv`\n\n"
        "4. Diagnostico GCV\n"
        "`/diagnostico_gcv`",
        parse_mode="Markdown",
    )


async def liberar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    texto = update.message.text.replace("\n", " ").replace("\r", " ").strip()

    try:
        nome, mac = extrair_nome_mac(texto)
    except Exception as e:
        await update.message.reply_text(f"Erro: {e}")
        return

    ticket = submit_job(
        "bluepex",
        "telegram",
        {"nome": nome, "mac": mac},
        lambda: liberar_visitante(nome, mac),
    )

    try:
        if ticket["position"] == 0:
            await update.message.reply_text(
                "🚀 *INICIANDO LIBERACAO BLUEPEX*\n\n"
                f"*Nome:* {md(nome)}\n"
                f"*MAC:* {md(mac)}\n\n"
                "Processando...",
                parse_mode="Markdown",
            )
        else:
            await update.message.reply_text(
                "⏳ *ADICIONADO NA FILA*\n\n"
                f"*Nome:* {md(nome)}\n"
                f"*MAC:* {md(mac)}\n"
                f"*Posicao:* {md(ticket['position'])}\n\n"
                "Aguarde a vez da automacao...",
                parse_mode="Markdown",
            )

        print(f"{AZUL}{NEGRITO}[BOT]{RESET} {CIANO}BluePex enfileirado...{RESET}")
        print(f"{AMARELO}Nome:{RESET} {nome}")
        print(f"{AMARELO}MAC:{RESET} {mac}")

        resultado = await asyncio.to_thread(wait_for_job, ticket)

        if resultado["sucesso"]:
            await update.message.reply_text(
                "✅ *LIBERACAO CONCLUIDA*\n\n"
                f"*Nome:* {md(resultado['nome'])}\n"
                f"*MAC:* {md(resultado['mac'])}\n"
                f"*IP:* {md(resultado['ip'])}\n\n"
                "Acesso liberado.",
                parse_mode="Markdown",
            )

            print(f"{VERDE}{NEGRITO}[SUCESSO]{RESET} {VERDE}Liberacao BluePex concluida{RESET}")
            print(f"{AMARELO}Nome:{RESET} {resultado['nome']}")
            print(f"{AMARELO}MAC:{RESET} {resultado['mac']}")
            print(f"{AMARELO}IP:{RESET} {resultado['ip']}")
        else:
            await update.message.reply_text(
                "⚠️ *FALHA NA LIBERACAO*\n\n"
                f"*Motivo:* {md(resultado['mensagem'])}",
                parse_mode="Markdown",
            )

            print(f"{VERMELHO}{NEGRITO}[FALHA]{RESET} {VERMELHO}Erro na liberacao BluePex{RESET}")
            print(f"{AMARELO}Motivo:{RESET} {resultado['mensagem']}")
    except Exception as e:
        await update.message.reply_text(f"Erro inesperado: {e}")
        print(f"{VERMELHO}{NEGRITO}[ERRO]{RESET} {e}")


async def consultor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    texto = update.message.text.replace("\n", " ").replace("\r", " ").strip()

    try:
        nome_consultor, data_limite = extrair_nome_data(texto)
    except Exception as e:
        await update.message.reply_text(f"Erro: {e}")
        return

    ticket = submit_job(
        "consultor",
        "telegram",
        {"nome": nome_consultor, "data_limite": data_limite},
        lambda: liberar_consultor(nome_consultor, data_limite),
    )

    try:
        if ticket["position"] == 0:
            await update.message.reply_text(
                "🚀 *INICIANDO LIBERACAO CONSULTOR*\n\n"
                f"*Consultor:* {md(nome_consultor)}\n"
                f"*Data limite:* {md(data_limite)}\n\n"
                "Processando...",
                parse_mode="Markdown",
            )
        else:
            await update.message.reply_text(
                "⏳ *ADICIONADO NA FILA*\n\n"
                f"*Consultor:* {md(nome_consultor)}\n"
                f"*Data limite:* {md(data_limite)}\n"
                f"*Posicao:* {md(ticket['position'])}\n\n"
                "Aguarde a vez da automacao...",
                parse_mode="Markdown",
            )

        print(f"{AZUL}{NEGRITO}[BOT]{RESET} {CIANO}Consultor enfileirado...{RESET}")
        print(f"{AMARELO}Consultor:{RESET} {nome_consultor}")
        print(f"{AMARELO}Data limite:{RESET} {data_limite}")

        resultado = await asyncio.to_thread(wait_for_job, ticket)

        if resultado["sucesso"]:
            await update.message.reply_text(
                "✅ *LIBERACAO DE CONSULTOR CONCLUIDA*\n\n"
                f"*Consultor:* {md(nome_consultor)}\n"
                f"*Data limite:* {md(data_limite)}\n\n"
                "Acesso liberado com sucesso.",
                parse_mode="Markdown",
            )

            print(f"{VERDE}{NEGRITO}[SUCESSO]{RESET} {VERDE}Liberacao de consultor concluida{RESET}")
            print(f"{AMARELO}Consultor:{RESET} {nome_consultor}")
            print(f"{AMARELO}Data limite:{RESET} {data_limite}")
        else:
            await update.message.reply_text(
                "⚠️ *FALHA NA LIBERACAO DO CONSULTOR*\n\n"
                f"*Motivo:* {md(resultado['mensagem'])}",
                parse_mode="Markdown",
            )

            print(f"{VERMELHO}{NEGRITO}[FALHA]{RESET} {VERMELHO}Erro na liberacao de consultor{RESET}")
            print(f"{AMARELO}Motivo:{RESET} {resultado['mensagem']}")
    except Exception as e:
        await update.message.reply_text(f"Erro inesperado: {e}")
        print(f"{VERMELHO}{NEGRITO}[ERRO]{RESET} {e}")


async def reiniciar_gcv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    if not chat_autorizado_gcv(update.effective_chat):
        await update.message.reply_text(
            "⛔ Comando permitido apenas nos grupos GCV autorizados."
        )
        return

    loop = asyncio.get_running_loop()
    notificar = criar_notificador_telegram(update, loop)
    user_id = update.effective_user.id if update.effective_user else None
    chat_id = update.effective_chat.id if update.effective_chat else None

    ticket = submit_job_once(
        "gcv_reinicio",
        "telegram",
        {"comando": "/reiniciar_gcv", "user_id": user_id, "chat_id": chat_id},
        lambda: reiniciar_robos_gcv(notificar),
    )

    if not ticket["accepted"]:
        await update.message.reply_text(
            "⚠️ Ja existe um reinicio dos robos GCV em execucao ou na fila."
        )
        return

    try:
        if ticket["position"] and ticket["position"] > 0:
            await update.message.reply_text(
                f"⏳ Reinicio dos robos GCV adicionado na fila. Posicao: {ticket['position']}."
            )

        print(f"{AZUL}{NEGRITO}[BOT]{RESET} {CIANO}Reinicio GCV enfileirado...{RESET}")
        print(f"{AMARELO}Usuario Telegram:{RESET} {user_id}")
        print(f"{AMARELO}Chat Telegram:{RESET} {chat_id}")

        resultado = await asyncio.to_thread(wait_for_job, ticket)

        if resultado.get("sucesso"):
            await enviar_print_telegram(update, resultado.get("screenshot_path"))
            mensagem = resultado.get("mensagem") or (
                "✅ Comando de inicialização dos robôs GCV executado com sucesso."
            )
            await update.message.reply_text(mensagem)
            print(f"{VERDE}{NEGRITO}[SUCESSO]{RESET} {VERDE}Reinicio GCV concluido{RESET}")
            return

        await enviar_print_telegram(update, resultado.get("screenshot_path"))

        mensagem = resultado.get("mensagem") or "Falha no reinicio dos robos GCV."
        await update.message.reply_text(mensagem)
        print(f"{VERMELHO}{NEGRITO}[FALHA]{RESET} {VERMELHO}Erro no reinicio GCV{RESET}")
        print(f"{AMARELO}Motivo:{RESET} {mensagem}")
    except Exception as e:
        await update.message.reply_text(f"Erro inesperado: {e}")
        print(f"{VERMELHO}{NEGRITO}[ERRO]{RESET} {e}")


async def diagnostico_gcv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    if not chat_autorizado_gcv(update.effective_chat):
        await update.message.reply_text(
            "⛔ Comando permitido apenas nos grupos GCV autorizados."
        )
        return

    try:
        resultado = await asyncio.to_thread(diagnosticar_gcv)
        linhas = [
            "Diagnostico GCV",
            "",
            _linha_diagnostico("Dependencias", resultado["dependencias"]),
            _linha_diagnostico("Executavel", resultado["executavel"]),
            _linha_diagnostico("Senha", resultado["senha"]),
            _linha_diagnostico("Sessao Windows", resultado["sessao"]),
            _linha_template_gcv("Parar Robôs", resultado["templates"]["parar_robos"]),
            _linha_template_gcv(
                "Monitorar Robôs",
                resultado["templates"]["monitorar_robos"],
            ),
            _linha_template_gcv(
                "Aviso robôs encerrados",
                resultado["templates"]["aviso_robos_encerrados"],
            ),
            _linha_template_gcv(
                "Terminal Parar Robôs",
                resultado["templates"]["terminal_parar_robos"],
            ),
            _linha_template_gcv(
                "Fechar RDP normal",
                resultado["templates"]["fechar_rdp_normal"],
            ),
            _linha_template_gcv(
                "Fechar RDP hover",
                resultado["templates"]["fechar_rdp_hover"],
            ),
            _linha_template_gcv(
                "Confirmacao desconexao RDP",
                resultado["templates"]["confirmacao_desconexao_rdp"],
            ),
            _linha_template_gcv(
                "OK desconexao RDP",
                resultado["templates"]["ok_desconexao_rdp"],
            ),
            "",
            resultado["mensagem"],
        ]

        await update.message.reply_text("\n".join(linhas))
        print(f"{AZUL}{NEGRITO}[BOT]{RESET} {CIANO}Diagnostico GCV executado{RESET}")
    except Exception as e:
        await update.message.reply_text(f"Erro inesperado no diagnostico GCV: {e}")
        print(f"{VERMELHO}{NEGRITO}[ERRO]{RESET} {e}")


def _linha_diagnostico(rotulo, item):
    marcador = "OK" if item.get("ok") else "FALHA"
    return f"{rotulo}: {marcador} - {item.get('mensagem', '-')}"


def _linha_template_gcv(rotulo, item):
    status = item.get("status") or ("encontrado" if item.get("ok") else "ausente")
    detalhe = item.get("mensagem")

    if detalhe:
        return f"Template {rotulo}: {status} - {detalhe}"

    return f"Template {rotulo}: {status}"


def main():
    init_history_store()
    init_job_queue()

    if not TOKEN:
        raise RuntimeError(
            f"{VERMELHO}{NEGRITO}TELEGRAM_BOT_TOKEN nao encontrado no .env{RESET}"
        )

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("liberar", liberar))
    app.add_handler(CommandHandler("consultor", consultor))
    app.add_handler(CommandHandler(["reiniciar_gcv", "reiniciar_robos"], reiniciar_gcv))
    app.add_handler(CommandHandler("diagnostico_gcv", diagnostico_gcv))

    print(f"{VERDE}{NEGRITO}Bot iniciado com sucesso...{RESET}")
    app.run_polling()


def run_telegram_bot():
    main()


if __name__ == "__main__":
    main()
