import os
import re
import time
import socket
import platform
import subprocess

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from bot_app.common.paths import ENV_PATH, IP_LIVRE_PATH, ensure_runtime_dirs

load_dotenv(dotenv_path=ENV_PATH, override=True)

# ================= CONFIG =================
BLUEPEX_URL_BASE = (os.getenv("BLUEPEX_URL") or "").rstrip("/")
URL_LOGIN = f"{BLUEPEX_URL_BASE}/" if BLUEPEX_URL_BASE else ""
URL_DHCP = f"{BLUEPEX_URL_BASE}/services_dhcp.php?if=opt2" if BLUEPEX_URL_BASE else ""
URL_LIBERACAO = f"{BLUEPEX_URL_BASE}/services_dhcp_edit.php?if=opt2" if BLUEPEX_URL_BASE else ""

USUARIO = os.getenv("BLUEPEX_USUARIO")
SENHA = os.getenv("BLUEPEX_SENHA")

REDE_BASE = "192.168"
RANGES = [7, 9]

# Não usar primeiro nem último IP do range
HOST_INICIO = 2
HOST_FIM = 253

TIMEOUT_MS = 1000
PING_FINAL_TIMEOUT_MS = 500
PING_FINAL_TENTATIVAS = 2
PING_FINAL_INTERVALO_S = 0.2
ARQUIVO_SAIDA = IP_LIVRE_PATH

HEADLESS = False

# Portas comuns para detectar IP ocupado mesmo sem responder ping
PORTAS_TESTE = [80, 443, 9100, 515, 631, 22, 23, 161, 445]
SOCKET_TIMEOUT = 0.5

ESPERA_PADRAO = 15
# =========================================


def validar_env_bluepex():
    variaveis = {
        "BLUEPEX_URL": BLUEPEX_URL_BASE,
        "BLUEPEX_USUARIO": USUARIO,
        "BLUEPEX_SENHA": SENHA,
    }

    faltando = [chave for chave, valor in variaveis.items() if not valor]

    if faltando:
        raise RuntimeError(
            f"Variaveis nao encontradas no .env: {', '.join(faltando)}"
        )


def iniciar_driver():
    options = webdriver.ChromeOptions()

    if HEADLESS:
        options.add_argument("--headless=new")

    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-blink-features=AutomationControlled")

    # Mantém o Chrome aberto mesmo após o script terminar

    return webdriver.Chrome(options=options)


def salvar_ip(ip):
    ensure_runtime_dirs()
    with open(ARQUIVO_SAIDA, "w", encoding="utf-8") as f:
        f.write(ip.strip() + "\n")


def ping(ip, timeout_ms=None):
    sistema = platform.system().lower()
    timeout_ms = TIMEOUT_MS if timeout_ms is None else timeout_ms

    if sistema == "windows":
        comando = ["ping", "-n", "1", "-w", str(timeout_ms), ip]
    else:
        timeout_s = str(max(1, timeout_ms // 1000))
        comando = ["ping", "-c", "1", "-W", timeout_s, ip]

    print(f"   -> Pingando {ip}...")

    try:
        resultado = subprocess.run(
            comando,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        if resultado.returncode == 0:
            print(f"   -> {ip} respondeu ping")
            return True
        else:
            print(f"   -> {ip} NÃO respondeu ping")
            return False

    except Exception as e:
        print(f"   -> Erro ao pingar {ip}: {e}")
        return False


def testar_porta(ip, porta, timeout=SOCKET_TIMEOUT):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)

    try:
        resultado = sock.connect_ex((ip, porta))
        return resultado == 0
    except Exception:
        return False
    finally:
        sock.close()


def ip_tem_servico_ativo(ip):
    print(f"   -> Testando portas em {ip}...")

    for porta in PORTAS_TESTE:
        aberta = testar_porta(ip, porta)
        if aberta:
            print(f"   -> Porta {porta} aberta em {ip}")
            return True

    print(f"   -> Nenhuma porta de teste respondeu em {ip}")
    return False


def confirmar_candidato_final(ip):
    print(f"[CONFIRMANDO CANDIDATO] {ip}")

    for tentativa in range(1, PING_FINAL_TENTATIVAS + 1):
        print(f"   -> Tentativa rápida {tentativa}/{PING_FINAL_TENTATIVAS}")

        if ping(ip, timeout_ms=PING_FINAL_TIMEOUT_MS):
            print(f"[OCUPADO PING FINAL] {ip} -> descartado")
            return False

        if tentativa < PING_FINAL_TENTATIVAS:
            time.sleep(PING_FINAL_INTERVALO_S)

    print(f"[CANDIDATO OK] {ip}")
    return True


def gerar_ips_candidatos():
    for terceiro_octeto in RANGES:
        for host in range(HOST_INICIO, HOST_FIM + 1):
            yield f"{REDE_BASE}.{terceiro_octeto}.{host}"


def tentar_login(driver):
    driver.get(URL_LOGIN)
    time.sleep(1.5)

    campo_usuario = None
    campo_senha = None

    seletores_usuario = [
        (By.NAME, "username"),
        (By.NAME, "user"),
        (By.ID, "username"),
        (By.ID, "user"),
        (By.XPATH, "//input[@type='text']"),
    ]

    seletores_senha = [
        (By.NAME, "password"),
        (By.NAME, "senha"),
        (By.ID, "password"),
        (By.ID, "senha"),
        (By.XPATH, "//input[@type='password']"),
    ]

    for by, valor in seletores_usuario:
        try:
            campo_usuario = driver.find_element(by, valor)
            if campo_usuario:
                break
        except NoSuchElementException:
            pass

    for by, valor in seletores_senha:
        try:
            campo_senha = driver.find_element(by, valor)
            if campo_senha:
                break
        except NoSuchElementException:
            pass

    if not campo_usuario or not campo_senha:
        raise RuntimeError("Não consegui localizar os campos de login.")

    campo_usuario.clear()
    campo_usuario.send_keys(USUARIO)

    campo_senha.clear()
    campo_senha.send_keys(SENHA)
    campo_senha.send_keys(Keys.ENTER)

    time.sleep(2.5)


def abrir_tela_dhcp_direto(driver):
    driver.get(URL_DHCP)
    time.sleep(2)

    WebDriverWait(driver, ESPERA_PADRAO).until(
        lambda d: "Endereço IP" in d.page_source or "Cliente" in d.page_source or "MAC" in d.page_source
    )


def extrair_ips_da_pagina(driver):
    ips_validos = set()

    prefixos_validos = [f"{REDE_BASE}.{terceiro_octeto}." for terceiro_octeto in RANGES]

    linhas = driver.find_elements(By.XPATH, "//table//tr")

    for linha in linhas:
        colunas = linha.find_elements(By.TAG_NAME, "td")

        if not colunas:
            continue

        for coluna in colunas:
            texto = coluna.text.strip()

            if re.fullmatch(r"(?:\d{1,3}\.){3}\d{1,3}", texto):
                if not any(texto.startswith(prefixo) for prefixo in prefixos_validos):
                    continue

                partes = texto.split(".")
                if len(partes) != 4:
                    continue

                try:
                    host = int(partes[3])
                except ValueError:
                    continue

                if HOST_INICIO <= host <= HOST_FIM:
                    ips_validos.add(texto)

    return ips_validos


def encontrar_primeiro_ip_realmente_livre(ips_no_firewall):
    for ip in gerar_ips_candidatos():
        if ip in ips_no_firewall:
            print(f"[NO FIREWALL] {ip} -> descartado")
            continue

        print(f"[CANDIDATO] {ip} -> ausente no firewall")

        if not confirmar_candidato_final(ip):
            continue

        print(f"[LIVRE] {ip}")
        return ip

    return None


def normalizar_mac(mac):
    mac = mac.strip().upper().replace("-", ":")

    if not re.fullmatch(r"^[0-9A-F]{2}(:[0-9A-F]{2}){5}$", mac):
        raise ValueError("MAC inválido. Use o formato AA:BB:CC:DD:EE:FF")

    return mac


def preencher_input(driver, elemento, valor):
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elemento)
    time.sleep(0.2)

    try:
        elemento.click()
    except Exception:
        driver.execute_script("arguments[0].click();", elemento)

    time.sleep(0.2)

    try:
        elemento.clear()
    except Exception:
        pass

    try:
        elemento.send_keys(Keys.CONTROL, "a")
        elemento.send_keys(Keys.DELETE)
    except Exception:
        pass

    elemento.send_keys(valor)
    time.sleep(0.2)


def abrir_tela_liberacao(driver):
    print("Abrindo tela de liberação...")
    driver.get(URL_LIBERACAO)

    WebDriverWait(driver, ESPERA_PADRAO).until(
        lambda d: "Editar mapeamento estático" in d.page_source
        or "Mapeamento DHCP estático" in d.page_source
    )

    print("Tela de liberação aberta com sucesso.")
    time.sleep(1)


def obter_tres_primeiros_inputs(driver):
    """
    Pela tela:
    1 = ENDEREÇO MAC
    2 = IDENTIFICADOR CLIENTE
    3 = ENDEREÇO IP
    """
    inputs = driver.find_elements(
        By.XPATH,
        "//input[not(@type='hidden') and not(@type='checkbox') and not(@type='submit') and not(@type='button')]"
    )

    visiveis = []
    for inp in inputs:
        try:
            if inp.is_displayed() and inp.is_enabled():
                visiveis.append(inp)
        except Exception:
            pass

    print(f"Inputs visíveis encontrados: {len(visiveis)}")

    if len(visiveis) < 3:
        raise RuntimeError(f"Não consegui localizar os 3 primeiros campos. Achei apenas {len(visiveis)}.")

    return visiveis[0], visiveis[1], visiveis[2]


def preencher_formulario_liberacao(driver, nome_visitante, mac_visitante, ip_livre):
    print("Localizando os 3 primeiros campos da tela de liberação...")

    campo_mac, campo_identificador, campo_ip = obter_tres_primeiros_inputs(driver)

    print("Preenchendo MAC...")
    preencher_input(driver, campo_mac, normalizar_mac(mac_visitante))

    print("Preenchendo IDENTIFICADOR CLIENTE...")
    preencher_input(driver, campo_identificador, nome_visitante)

    print("Preenchendo IP...")
    preencher_input(driver, campo_ip, ip_livre)

    mac_preenchido = (campo_mac.get_attribute("value") or "").strip()
    identificador_preenchido = (campo_identificador.get_attribute("value") or "").strip()
    ip_preenchido = (campo_ip.get_attribute("value") or "").strip()

    print(f"   MAC preenchido: {mac_preenchido}")
    print(f"   IDENTIFICADOR preenchido: {identificador_preenchido}")
    print(f"   IP preenchido: {ip_preenchido}")

    if mac_preenchido != normalizar_mac(mac_visitante):
        raise RuntimeError("Falha ao preencher o campo MAC.")

    if identificador_preenchido != nome_visitante:
        raise RuntimeError("Falha ao preencher o campo IDENTIFICADOR CLIENTE.")

    if ip_preenchido != ip_livre:
        raise RuntimeError("Falha ao preencher o campo IP.")

    return campo_ip


def salvar_primeira_etapa_com_enter(campo_ip):
    print("Enviando ENTER para salvar os dados do formulário...")
    try:
        campo_ip.click()
    except Exception:
        pass

    time.sleep(0.3)
    campo_ip.send_keys(Keys.ENTER)
    time.sleep(2)


def aguardar_retorno_para_tela_dhcp(driver):
    print("Aguardando retorno para a tela do mapa DHCP...")

    WebDriverWait(driver, ESPERA_PADRAO).until(
        lambda d: "services_dhcp.php?if=opt2" in d.current_url.lower()
        or "Servidor DHCP" in d.page_source
        or "OPT2_DHCP" in d.page_source
    )

    print("Retornou para a tela DHCP.")
    time.sleep(1.5)


def clicar_aplicar_mudancas(driver):
    print("Procurando botão verde 'Aplicar mudanças'...")

    seletores = [
        (By.XPATH, "//button[contains(., 'Aplicar mudanças')]"),
        (By.XPATH, "//input[contains(@value, 'Aplicar mudanças')]"),
        (By.XPATH, "//a[contains(., 'Aplicar mudanças')]"),
        (By.XPATH, "//button[contains(., 'Aplicar')]"),
        (By.XPATH, "//input[contains(@value, 'Aplicar')]"),
        (By.XPATH, "//a[contains(., 'Aplicar')]"),
        (By.XPATH, "//*[contains(@class,'btn-success') and contains(., 'Aplicar')]"),
        (By.XPATH, "//*[contains(@class,'btn-success') and contains(., 'mudan')]"),
    ]

    botao = None

    for by, valor in seletores:
        try:
            elementos = driver.find_elements(by, valor)
            for el in elementos:
                if el.is_displayed() and el.is_enabled():
                    botao = el
                    break
            if botao:
                break
        except Exception:
            pass

    if not botao:
        raise RuntimeError("Não consegui localizar o botão 'Aplicar mudanças'.")

    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", botao)
    time.sleep(0.5)

    try:
        botao.click()
    except Exception:
        driver.execute_script("arguments[0].click();", botao)

    print("Botão 'Aplicar mudanças' clicado.")
    time.sleep(3)


def liberar_visitante(nome_visitante, mac_visitante):
    driver = None
    fechar_driver_no_final = False

    try:
        validar_env_bluepex()

        nome_visitante = (nome_visitante or "").strip()
        if not nome_visitante:
            return {
                "sucesso": False,
                "nome": nome_visitante,
                "mac": mac_visitante,
                "ip": None,
                "mensagem": "Nome do visitante não pode ficar vazio."
            }

        mac_visitante = normalizar_mac(mac_visitante)

        print("Iniciando navegador...")
        driver = iniciar_driver()

        print("Fazendo login...")
        tentar_login(driver)

        print("Abrindo tela DHCP direto...")
        abrir_tela_dhcp_direto(driver)

        print("Coletando IPs visíveis no firewall...")
        ips_no_firewall = extrair_ips_da_pagina(driver)
        print(f"IPs encontrados no firewall: {len(ips_no_firewall)}")

        for ip in sorted(ips_no_firewall):
            print(f" - {ip}")

        print("Procurando primeiro IP realmente livre...")
        ip_livre = encontrar_primeiro_ip_realmente_livre(ips_no_firewall)

        if not ip_livre:
            salvar_ip("NENHUM_IP_LIVRE")
            return {
                "sucesso": False,
                "nome": nome_visitante,
                "mac": mac_visitante,
                "ip": None,
                "mensagem": "Nenhum IP realmente livre encontrado."
            }

        salvar_ip(ip_livre)
        print(f"IP LIVRE ENCONTRADO: {ip_livre}")

        print("Abrindo tela de liberação...")
        abrir_tela_liberacao(driver)

        print("Preenchendo formulário...")
        campo_ip = preencher_formulario_liberacao(
            driver=driver,
            nome_visitante=nome_visitante,
            mac_visitante=mac_visitante,
            ip_livre=ip_livre
        )

        print("Salvando primeira etapa...")
        salvar_primeira_etapa_com_enter(campo_ip)

        print("Esperando voltar para a tela DHCP...")
        aguardar_retorno_para_tela_dhcp(driver)

        print("Aplicando mudanças...")
        clicar_aplicar_mudancas(driver)

        print("Liberação concluída com sucesso.")
        print(f"Visitante: {nome_visitante}")
        print(f"MAC: {mac_visitante}")
        fechar_driver_no_final = True
        print(f"IP liberado: {ip_livre}")
        print("O script terminou. O Chrome permanecerá aberto.")

        return {
            "sucesso": True,
            "nome": nome_visitante,
            "mac": mac_visitante,
            "ip": ip_livre,
            "mensagem": "Liberação concluída com sucesso."
        }

    except TimeoutException:
        salvar_ip("ERRO_TIMEOUT")
        return {
            "sucesso": False,
            "nome": nome_visitante if 'nome_visitante' in locals() else "",
            "mac": mac_visitante if 'mac_visitante' in locals() else "",
            "ip": None,
            "mensagem": "Erro: tempo esgotado."
        }

    except Exception as e:
        salvar_ip("ERRO_AUTOMACAO")
        return {
            "sucesso": False,
            "nome": nome_visitante if 'nome_visitante' in locals() else "",
            "mac": mac_visitante if 'mac_visitante' in locals() else "",
            "ip": None,
            "mensagem": f"Erro durante a execução: {e}"
        }

    finally:
        # Não fecha o Chrome. Como usamos detach=True,
        # ele permanece aberto após o fim do script.
        if driver and fechar_driver_no_final:
            try:
                driver.quit()
            except Exception:
                pass


def main():
    """
    Teste local sem bot.
    Altere somente estes dois valores quando quiser testar manualmente.
    """
    nome_teste = "HENDEL-CEL"
    mac_teste = "14:05:89:F3:1C:62"

    resultado = liberar_visitante(nome_teste, mac_teste)

    print("\n========== RESULTADO FINAL ==========")
    print(resultado)


if __name__ == "__main__":
    main()
