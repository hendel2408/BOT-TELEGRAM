import os
import re
import time
from datetime import datetime

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.common.exceptions import (
    TimeoutException,
    StaleElementReferenceException,
    WebDriverException,
)

from bot_app.common.paths import ENV_PATH

load_dotenv(dotenv_path=ENV_PATH, override=True)

# =========================================================
# CONFIGURAÇÕES VIA .ENV
# =========================================================
URL_LOGIN = os.getenv("CS_URL_LOGIN")
USUARIO = os.getenv("CS_USER")
SENHA = os.getenv("CS_PASSWORD")

HEADLESS = False
TEMPO_PADRAO = 20
TIME_SLEEP_CURTO = 0.4
TIME_SLEEP_MEDIO = 1
TIME_SLEEP_LONGO = 2

# =========================================================
# CORES TERMINAL
# =========================================================
RESET = "\033[0m"
VERDE = "\033[92m"
VERMELHO = "\033[91m"
AMARELO = "\033[93m"
AZUL = "\033[94m"
CIANO = "\033[96m"
NEGRITO = "\033[1m"


# =========================================================
# LOGS
# =========================================================
def log(msg: str):
    print(f"{AZUL}{NEGRITO}[INFO]{RESET} {CIANO}{msg}{RESET}")


def ok(msg: str):
    print(f"{VERDE}{NEGRITO}[OK]{RESET} {msg}")


def alerta(msg: str):
    print(f"{AMARELO}{NEGRITO}[ALERTA]{RESET} {msg}")


def erro(msg: str):
    print(f"{VERMELHO}{NEGRITO}[ERRO]{RESET} {msg}")


# =========================================================
# VALIDAÇÕES
# =========================================================
def validar_env():
    variaveis = {
        "CS_URL_LOGIN": URL_LOGIN,
        "CS_USER": USUARIO,
        "CS_PASSWORD": SENHA,
    }

    faltando = [chave for chave, valor in variaveis.items() if not valor]

    if faltando:
        raise RuntimeError(
            f"Variáveis não encontradas no .env: {', '.join(faltando)}"
        )


def validar_data_limite(data_limite: str):
    if not data_limite or not data_limite.strip():
        raise ValueError("Data limite não informada.")

    data_limite = data_limite.strip()

    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", data_limite):
        raise ValueError("Data limite inválida. Use o formato DD/MM/AAAA.")

    try:
        datetime.strptime(data_limite, "%d/%m/%Y")
    except ValueError:
        raise ValueError("Data limite inválida. Verifique dia, mês e ano.")

    return data_limite


# =========================================================
# DRIVER
# =========================================================
def iniciar_driver():
    options = webdriver.ChromeOptions()

    if HEADLESS:
        options.add_argument("--headless=new")

    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-popup-blocking")
    options.add_experimental_option("detach", True)

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(60)
    return driver


def esperar(driver, tempo=TEMPO_PADRAO):
    return WebDriverWait(driver, tempo)


# =========================================================
# AUXILIARES GENÉRICOS
# =========================================================
def scroll_centro(driver, elemento):
    try:
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center', inline: 'center'});",
            elemento
        )
        time.sleep(TIME_SLEEP_CURTO)
    except Exception:
        pass


def clicar_seguro(driver, elemento):
    scroll_centro(driver, elemento)

    try:
        elemento.click()
    except Exception:
        driver.execute_script("arguments[0].click();", elemento)

    time.sleep(0.6)


def preencher_input(elemento, valor: str):
    try:
        elemento.click()
    except Exception:
        pass

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

    elemento.send_keys(str(valor))
    time.sleep(0.4)


def encontrar_primeiro_visivel(driver, seletores, timeout=8):
    fim = time.time() + timeout

    while time.time() < fim:
        for by, valor in seletores:
            try:
                elementos = driver.find_elements(by, valor)
                for el in elementos:
                    try:
                        if el.is_displayed():
                            return el
                    except StaleElementReferenceException:
                        continue
            except Exception:
                continue
        time.sleep(0.3)

    return None


def encontrar_todos_visiveis(driver, seletores, timeout=8):
    fim = time.time() + timeout

    while time.time() < fim:
        encontrados = []
        for by, valor in seletores:
            try:
                elementos = driver.find_elements(by, valor)
                for el in elementos:
                    try:
                        if el.is_displayed():
                            encontrados.append(el)
                    except StaleElementReferenceException:
                        continue
            except Exception:
                continue

        if encontrados:
            return encontrados

        time.sleep(0.3)

    return []


def clicar_por_texto(driver, texto: str, timeout=10):
    log(f'Tentando clicar em "{texto}"...')

    texto_norm = texto.strip()

    seletores = [
        (By.XPATH, f"//button[contains(normalize-space(.), '{texto_norm}')]"),
        (By.XPATH, f"//a[contains(normalize-space(.), '{texto_norm}')]"),
        (By.XPATH, f"//span[contains(normalize-space(.), '{texto_norm}')]"),
        (By.XPATH, f"//*[contains(normalize-space(text()), '{texto_norm}')]"),
        (By.XPATH, f"//*[@title='{texto_norm}']"),
        (By.XPATH, f"//*[@aria-label='{texto_norm}']"),
        (By.XPATH, f"//*[contains(@aria-label, '{texto_norm}')]"),
        (By.XPATH, f"//*[contains(@title, '{texto_norm}')]"),
    ]

    elemento = encontrar_primeiro_visivel(driver, seletores, timeout=timeout)

    if not elemento:
        raise RuntimeError(f'Não consegui localizar o botão/texto "{texto}".')

    clicar_seguro(driver, elemento)
    ok(f'Clique realizado em "{texto}".')


def selecionar_select_por_elemento(select_el, valor: str):
    try:
        Select(select_el).select_by_visible_text(valor)
        return True
    except Exception:
        pass

    try:
        opcoes = Select(select_el).options
        for opcao in opcoes:
            texto = opcao.text.strip().lower()
            if texto == valor.strip().lower():
                Select(select_el).select_by_visible_text(opcao.text)
                return True
    except Exception:
        pass

    try:
        Select(select_el).select_by_index(1)
        return True
    except Exception:
        pass

    return False


# =========================================================
# LOGIN
# =========================================================
def fazer_login(driver):
    if USUARIO is None or SENHA is None:
        raise RuntimeError("Credenciais do CS nao foram carregadas do .env.")

    log("Abrindo tela de login...")
    driver.get(URL_LOGIN)
    time.sleep(3)

    log("Procurando campos de login...")

    campo_usuario = encontrar_primeiro_visivel(
        driver,
        [
            (By.NAME, "P9999_USERNAME"),
            (By.ID, "P9999_USERNAME"),
            (By.NAME, "username"),
            (By.ID, "username"),
            (By.XPATH, "//input[@type='text']"),
            (By.XPATH, "//input[@type='email']"),
        ],
        timeout=10,
    )

    campo_senha = encontrar_primeiro_visivel(
        driver,
        [
            (By.NAME, "P9999_PASSWORD"),
            (By.ID, "P9999_PASSWORD"),
            (By.NAME, "password"),
            (By.ID, "password"),
            (By.XPATH, "//input[@type='password']"),
        ],
        timeout=10,
    )

    if not campo_usuario or not campo_senha:
        raise RuntimeError("Não consegui localizar os campos de login.")

    preencher_input(campo_usuario, USUARIO)
    preencher_input(campo_senha, SENHA)

    log("Enviando login...")
    campo_senha.send_keys(Keys.ENTER)
    time.sleep(4)

    ok("Login enviado com sucesso.")


# =========================================================
# NAVEGAÇÃO
# =========================================================
def abrir_tela_seguranca(driver):
    log('Procurando link EXATO do módulo Segurança...')

    seletor = "//a[contains(@href, 'cs-seguranca/home') and normalize-space(.)='Segurança']"

    try:
        elemento = WebDriverWait(driver, 15).until(
            lambda d: next(
                (
                    el for el in d.find_elements(By.XPATH, seletor)
                    if el.is_displayed() and el.is_enabled()
                ),
                None
            )
        )

        if not elemento:
            raise RuntimeError("Elemento encontrado, mas não está visível.")

        log(f'Elemento correto encontrado: href={elemento.get_attribute("href")}')
        clicar_seguro(driver, elemento)
        time.sleep(3)

        ok('Entrou no módulo Segurança com sucesso.')

    except Exception as e:
        raise RuntimeError(f'Falha ao clicar no módulo Segurança: {e}')


def abrir_liberar_acesso_externo(driver):
    clicar_por_texto(driver, "Navegação Principal", timeout=12)
    time.sleep(TIME_SLEEP_MEDIO)

    clicar_por_texto(driver, "Processos", timeout=12)
    time.sleep(TIME_SLEEP_MEDIO)

    clicar_por_texto(driver, "Liberar Acesso Externo", timeout=12)
    time.sleep(3)

    ok("Tela 'Liberar Acesso Externo' aberta.")


# =========================================================
# TELA LIBERAR ACESSO EXTERNO
# =========================================================
def remover_filtro_liberado(driver):
    log('Tentando remover o filtro "Liberado" pelo X...')

    seletores = [
        (By.XPATH, "//span[normalize-space(.)='Liberado']/following::span[contains(@class,'icon-remove')][1]"),
        (By.XPATH, "//*[.//span[normalize-space(.)='Liberado']]//span[contains(@class,'icon-remove')]"),
        (By.XPATH, "//*[contains(@class,'icon-remove') and ancestor::*[contains(., 'Liberado')]]"),
    ]

    botao_remover = encontrar_primeiro_visivel(driver, seletores, timeout=5)

    if not botao_remover:
        alerta('Filtro "Liberado" não encontrado ou já removido.')
        return

    clicar_seguro(driver, botao_remover)
    time.sleep(1.5)

    ok('Filtro "Liberado" removido com sucesso pelo X.')


def localizar_checkbox_marcar_todos(driver):
    log("Procurando caixa de seleção do card Usuários...")

    seletores = [
        (By.XPATH, "//th//input[@type='checkbox']"),
        (By.XPATH, "//thead//input[@type='checkbox']"),
        (By.XPATH, "//input[@type='checkbox']"),
        (By.XPATH, "//span[contains(@class,'checkbox')]"),
        (By.XPATH, "//div[contains(@class,'checkbox')]"),
    ]

    elemento = encontrar_primeiro_visivel(driver, seletores, timeout=10)

    if not elemento:
        raise RuntimeError(
            "Não consegui localizar a caixa de seleção do card Usuários."
        )

    ok("Caixa de seleção localizada.")
    return elemento


def localizar_input_pesquisa(driver):
    log("Procurando input de pesquisa...")

    seletores = [
        (By.XPATH, "//input[contains(@placeholder, 'Pesquisa')]"),
        (By.XPATH, "//input[contains(@placeholder, 'pesquisa')]"),
        (By.XPATH, "//input[contains(@aria-label, 'Pesquisa')]"),
        (By.XPATH, "//input[contains(@aria-label, 'pesquisa')]"),
        (By.XPATH, "//input[contains(@title, 'Pesquisa')]"),
        (By.XPATH, "//input[contains(@title, 'pesquisa')]"),
        (By.XPATH, "//input[@type='search']"),
        (By.XPATH, "(//input[@type='text'])[1]"),
    ]

    campo = encontrar_primeiro_visivel(driver, seletores, timeout=10)

    if not campo:
        raise RuntimeError("Não consegui localizar o campo de pesquisa.")

    ok("Campo de pesquisa localizado.")
    return campo


def pesquisar_consultor(driver, nome_consultor: str):
    log(f'Pesquisando consultor "{nome_consultor}"...')

    campo_pesquisa = localizar_input_pesquisa(driver)
    preencher_input(campo_pesquisa, nome_consultor.strip())
    campo_pesquisa.send_keys(Keys.ENTER)
    time.sleep(2)

    ok("Pesquisa executada.")
    return campo_pesquisa


def clicar_consultor_encontrado(driver, nome_consultor: str):
    log(f'Procurando consultor "{nome_consultor}" na lista...')

    nome = nome_consultor.strip()

    seletores = [
        (By.XPATH, f"//td[contains(normalize-space(.), '{nome}')]"),
        (By.XPATH, f"//a[contains(normalize-space(.), '{nome}')]"),
        (By.XPATH, f"//*[contains(normalize-space(text()), '{nome}')]"),
    ]

    fim = time.time() + 12

    while time.time() < fim:
        for by, valor in seletores:
            try:
                elementos = driver.find_elements(by, valor)

                for el in elementos:
                    try:
                        if not el.is_displayed():
                            continue

                        clicar_seguro(driver, el)
                        ok(f'Consultor "{nome_consultor}" clicado.')
                        return True  # clicou e já sai para o próximo card

                    except StaleElementReferenceException:
                        continue
                    except Exception:
                        continue

            except Exception:
                continue

        time.sleep(0.4)

    raise RuntimeError(f'Não consegui clicar no consultor "{nome_consultor}".')


def selecionar_valor_combo_por_label(driver, label_texto: str, valor: str):
    log(f'Configurando "{label_texto}" para "{valor}"...')

    xpaths = [
        f"//label[contains(normalize-space(.), '{label_texto}')]/following::select[1]",
        f"//*[contains(normalize-space(.), '{label_texto}')]/following::select[1]",
    ]

    select_el = None

    for xp in xpaths:
        try:
            elementos = driver.find_elements(By.XPATH, xp)
            for el in elementos:
                if el.is_displayed():
                    select_el = el
                    break
            if select_el:
                break
        except Exception:
            continue

    if not select_el:
        raise RuntimeError(f'Não consegui localizar o select de "{label_texto}".')

    scroll_centro(driver, select_el)

    if not selecionar_select_por_elemento(select_el, valor):
        raise RuntimeError(f'Falha ao selecionar "{valor}" em "{label_texto}".')

    ok(f'Campo "{label_texto}" configurado para "{valor}".')


def preencher_data_limite(driver, data_limite: str):
    log(f'Preenchendo "Data Limite Acesso" com "{data_limite}"...')

    xpaths = [
        "//label[contains(normalize-space(.), 'Data Limite Acesso')]/following::input[1]",
        "//*[contains(normalize-space(.), 'Data Limite Acesso')]/following::input[1]",
        "//label[contains(normalize-space(.), 'Data limite acesso')]/following::input[1]",
        "//*[contains(normalize-space(.), 'Data limite acesso')]/following::input[1]",
        "//label[contains(normalize-space(.), 'Data Limite')]/following::input[1]",
        "//*[contains(normalize-space(.), 'Data Limite')]/following::input[1]",
    ]

    campo = None

    for xp in xpaths:
        try:
            elementos = driver.find_elements(By.XPATH, xp)
            for el in elementos:
                if el.is_displayed():
                    campo = el
                    break
            if campo:
                break
        except Exception:
            continue

    if not campo:
        raise RuntimeError("Não consegui localizar o campo Data Limite Acesso.")

    scroll_centro(driver, campo)
    preencher_input(campo, data_limite)
    ok("Data Limite Acesso preenchida.")


def clicar_processar(driver):
    log('Tentando clicar em "Processar"...')

    seletores = [
        (By.XPATH, "//button[contains(normalize-space(.), 'Processar')]"),
        (By.XPATH, "//a[contains(normalize-space(.), 'Processar')]"),
        (By.XPATH, "//*[@title='Processar']"),
        (By.XPATH, "//*[contains(@aria-label, 'Processar')]"),
        (By.XPATH, "//*[contains(normalize-space(text()), 'Processar')]"),
    ]

    botao = encontrar_primeiro_visivel(driver, seletores, timeout=10)

    if not botao:
        raise RuntimeError('Não consegui localizar o botão "Processar".')

    clicar_seguro(driver, botao)
    ok('Botão "Processar" clicado.')


def confirmar_janela_com_enter(driver):
    log("Aguardando janela de confirmação...")
    time.sleep(2)

    try:
        body = driver.find_element(By.TAG_NAME, "body")
        body.send_keys(Keys.ENTER)
        ok("Janela confirmada com ENTER.")
    except Exception as e:
        raise RuntimeError(f"Não consegui confirmar a janela com ENTER: {e}")


# =========================================================
# FLUXO PRINCIPAL
# =========================================================
def liberar_consultor(nome_consultor: str, data_limite: str):
    driver = None

    try:
        validar_env()

        if not nome_consultor or not nome_consultor.strip():
            return {
                "sucesso": False,
                "mensagem": "Nome do consultor não informado."
            }

        data_limite = validar_data_limite(data_limite)

        driver = iniciar_driver()

        fazer_login(driver)
        abrir_tela_seguranca(driver)
        abrir_liberar_acesso_externo(driver)

        remover_filtro_liberado(driver)
        time.sleep(TIME_SLEEP_MEDIO)

        checkbox = localizar_checkbox_marcar_todos(driver)
        clicar_seguro(driver, checkbox)

        pesquisar_consultor(driver, nome_consultor.strip())
        clicar_consultor_encontrado(driver, nome_consultor.strip())

        selecionar_valor_combo_por_label(driver, "Conexão", "Liberado")
        selecionar_valor_combo_por_label(driver, "Select", "Liberado")
        selecionar_valor_combo_por_label(driver, "Insert/Update/Delete", "Liberado")
        selecionar_valor_combo_por_label(driver, "Alteração de Objeto", "Liberado")

        preencher_data_limite(driver, data_limite)

        clicar_processar(driver)
        confirmar_janela_com_enter(driver)

        return {
            "sucesso": True,
            "mensagem": f'Consultor "{nome_consultor}" liberado com sucesso até {data_limite}.'
        }

    except TimeoutException:
        erro("Tempo esgotado durante a automação.")
        return {
            "sucesso": False,
            "mensagem": "Tempo esgotado durante a automação."
        }

    except ValueError as e:
        erro(str(e))
        return {
            "sucesso": False,
            "mensagem": str(e)
        }

    except WebDriverException as e:
        erro(f"Erro do navegador/Selenium: {e}")
        return {
            "sucesso": False,
            "mensagem": f"Erro do navegador/Selenium: {e}"
        }

    except Exception as e:
        erro(f"Erro durante a automação: {e}")
        return {
            "sucesso": False,
            "mensagem": f"Erro durante a automação: {e}"
        }

    finally:
        FECHAR_NO_FINAL = False

        if driver and FECHAR_NO_FINAL:
            try:
                driver.quit()
            except Exception:
                pass


# =========================================================
# TESTE LOCAL
# =========================================================
if __name__ == "__main__":
    nome = "CSCELSO"
    data = "28/04/2026"

    resultado = liberar_consultor(nome, data)
    print(resultado)
