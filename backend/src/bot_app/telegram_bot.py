import asyncio
import os
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from bot_app.automations.bluepex import liberar_visitante
from bot_app.automations.consultor_cs import liberar_consultor
from bot_app.common.paths import ENV_PATH
from bot_app.services.history_store import init_history_store
from bot_app.services.job_queue import init_job_queue, submit_job, wait_for_job

load_dotenv(dotenv_path=ENV_PATH, override=True)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

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


def extrair_nome_mac(texto: str):
    bruto = texto.replace("/liberar", "", 1).strip()
    bruto = bruto.replace("\n", " ").replace("\r", " ")

    if "|" not in bruto:
        raise ValueError(
            "🟥 FORMATO INVÁLIDO\n\n"
            "📌 Use corretamente:\n"
            "🟦 /liberar Nome do Visitante | AA:BB:CC:DD:EE:FF"
        )

    nome, mac = bruto.split("|", 1)

    nome = nome.strip()
    mac = mac.strip()

    if not nome:
        raise ValueError("🟥 Nome do visitante não informado.")
    if not mac:
        raise ValueError("🟥 Endereço MAC não informado.")

    return nome, mac


def extrair_nome_data(texto: str):
    bruto = texto.replace("/consultor", "", 1).strip()

    if "|" not in bruto:
        raise ValueError("Formato inválido. Use: /consultor Nome | DD/MM/AAAA")

    nome, data = bruto.split("|", 1)  # 👈 MUITO IMPORTANTE

    nome = nome.strip()
    data = data.strip()

    if not nome:
        raise ValueError("Nome não informado.")

    if not data:
        raise ValueError("Data não informada.")

    return nome, data


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🟢 *BOT ONLINE* 🟢\n\n"
        "🚀 Sistema de automações ativo\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📌 *COMANDOS DISPONÍVEIS:*\n\n"
        "1️⃣ *Liberar visitante no BluePex*\n"
        "`/liberar Nome do Visitante / AA:BB:CC:DD:EE:FF`\n\n"
        "💡 *Exemplo:*\n"
        "`/liberar João Silva / 00:11:22:33:44:55`\n\n"
        "2️⃣ *Liberar consultor no CS*\n"
        "`/consultor NOME_DO_CONSULTOR / DD/MM/AAAA`\n\n"
        "💡 *Exemplo:*\n"
        "`/consultor CSCELSO / 28/04/2026`\n"
        "━━━━━━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown"
    )


async def liberar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    texto = update.message.text.replace("\n", " ").replace("\r", " ").strip()

    try:
        nome, mac = extrair_nome_mac(texto)
    except Exception as e:
        await update.message.reply_text(f"❌ {e}")
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
                f"🔵 *INICIANDO LIBERAÇÃO BLUEPEX*\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 *Nome:* {nome}\n"
                f"💻 *MAC:* {mac}\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                "⏳ Processando...",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                f"🟡 *ADICIONADO NA FILA*\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 *Nome:* {nome}\n"
                f"💻 *MAC:* {mac}\n"
                f"📍 *Posição:* {ticket['position']}\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                "⏳ Aguarde a vez da automação...",
                parse_mode="Markdown"
            )

        print(f"{AZUL}{NEGRITO}[BOT]{RESET} {CIANO}BluePex enfileirado...{RESET}")
        print(f"{AMARELO}Nome:{RESET} {nome}")
        print(f"{AMARELO}MAC:{RESET} {mac}")

        resultado = await asyncio.to_thread(wait_for_job, ticket)

        if resultado["sucesso"]:
            await update.message.reply_text(
                "🟢 *LIBERAÇÃO CONCLUÍDA*\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 *Nome:* {resultado['nome']}\n"
                f"💻 *MAC:* {resultado['mac']}\n"
                f"🌐 *IP:* {resultado['ip']}\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                "✅ Acesso liberado!",
                parse_mode="Markdown"
            )

            print(f"{VERDE}{NEGRITO}[SUCESSO]{RESET} {VERDE}Liberação BluePex concluída{RESET}")
            print(f"{AMARELO}Nome:{RESET} {resultado['nome']}")
            print(f"{AMARELO}MAC:{RESET} {resultado['mac']}")
            print(f"{AMARELO}IP:{RESET} {resultado['ip']}")

        else:
            await update.message.reply_text(
                "🟥 *FALHA NA LIBERAÇÃO*\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⚠️ *Motivo:* {resultado['mensagem']}\n"
                "━━━━━━━━━━━━━━━━━━━━━━━",
                parse_mode="Markdown"
            )

            print(f"{VERMELHO}{NEGRITO}[FALHA]{RESET} {VERMELHO}Erro na liberação BluePex{RESET}")
            print(f"{AMARELO}Motivo:{RESET} {resultado['mensagem']}")

    except Exception as e:
        await update.message.reply_text(f"🚨 Erro inesperado: {e}")
        print(f"{VERMELHO}{NEGRITO}[ERRO]{RESET} {e}")


async def consultor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    texto = update.message.text.replace("\n", " ").replace("\r", " ").strip()

    try:
        nome_consultor, data_limite = extrair_nome_data(texto)
    except Exception as e:
        await update.message.reply_text(f"❌ {e}")
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
                f"🔵 *INICIANDO LIBERAÇÃO CONSULTOR*\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 *Consultor:* {nome_consultor}\n"
                f"📅 *Data limite:* {data_limite}\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                "⏳ Processando...",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                f"🟡 *ADICIONADO NA FILA*\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 *Consultor:* {nome_consultor}\n"
                f"📅 *Data limite:* {data_limite}\n"
                f"📍 *Posição:* {ticket['position']}\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                "⏳ Aguarde a vez da automação...",
                parse_mode="Markdown"
            )

        print(f"{AZUL}{NEGRITO}[BOT]{RESET} {CIANO}Consultor enfileirado...{RESET}")
        print(f"{AMARELO}Consultor:{RESET} {nome_consultor}")
        print(f"{AMARELO}Data limite:{RESET} {data_limite}")

        resultado = await asyncio.to_thread(wait_for_job, ticket)

        if resultado["sucesso"]:
            await update.message.reply_text(
                "🟢 *LIBERAÇÃO DE CONSULTOR CONCLUÍDA*\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 *Consultor:* {nome_consultor}\n"
                f"📅 *Data limite:* {data_limite}\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                "✅ Acesso liberado com sucesso!",
                parse_mode="Markdown"
            )

            print(f"{VERDE}{NEGRITO}[SUCESSO]{RESET} {VERDE}Liberação de consultor concluída{RESET}")
            print(f"{AMARELO}Consultor:{RESET} {nome_consultor}")
            print(f"{AMARELO}Data limite:{RESET} {data_limite}")

        else:
            await update.message.reply_text(
                "🟥 *FALHA NA LIBERAÇÃO DO CONSULTOR*\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⚠️ *Motivo:* {resultado['mensagem']}\n"
                "━━━━━━━━━━━━━━━━━━━━━━━",
                parse_mode="Markdown"
            )

            print(f"{VERMELHO}{NEGRITO}[FALHA]{RESET} {VERMELHO}Erro na liberação de consultor{RESET}")
            print(f"{AMARELO}Motivo:{RESET} {resultado['mensagem']}")

    except Exception as e:
        await update.message.reply_text(f"🚨 Erro inesperado: {e}")
        print(f"{VERMELHO}{NEGRITO}[ERRO]{RESET} {e}")


def main():
    init_history_store()
    init_job_queue()

    if not TOKEN:
        raise RuntimeError(
            f"{VERMELHO}{NEGRITO}TELEGRAM_BOT_TOKEN não encontrado no .env{RESET}"
        )

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("liberar", liberar))
    app.add_handler(CommandHandler("consultor", consultor))

    print(f"{VERDE}{NEGRITO}🤖 Bot iniciado com sucesso...{RESET}")
    app.run_polling()


def run_telegram_bot():
    main()


if __name__ == "__main__":
    main()
