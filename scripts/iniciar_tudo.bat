@echo off
setlocal EnableExtensions
chcp 65001 >nul
title BOT Telegram - Backend, Painel e GCV

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PROJECT_DIR=%%~fI"

set "VENV_DIR=%PROJECT_DIR%\.venv"
set "PYTHON_BIN=%VENV_DIR%\Scripts\python.exe"
set "BACKEND_DIR=%PROJECT_DIR%\backend"
set "BACKEND_ENV=%BACKEND_DIR%\.env"
set "BACKEND_MAIN=%BACKEND_DIR%\main.py"
set "BACKEND_SRC=%BACKEND_DIR%\src"
set "TELEGRAM_BOT=%BACKEND_SRC%\bot_app\telegram_bot.py"
set "WEB_PANEL=%BACKEND_SRC%\bot_app\web\panel.py"
set "GCV_AUTOMATION=%BACKEND_SRC%\bot_app\automations\gcv_robos.py"

call :assert_dir "%VENV_DIR%" "Pasta .venv nao encontrada na raiz do projeto." || exit /b 1
call :assert_file "%PYTHON_BIN%" "Python do ambiente virtual nao encontrado." || exit /b 1
call :assert_file "%BACKEND_ENV%" "Arquivo backend\.env nao encontrado." || exit /b 1
call :assert_file "%BACKEND_MAIN%" "Arquivo principal backend\main.py nao encontrado." || exit /b 1
call :assert_file "%TELEGRAM_BOT%" "Arquivo do bot Telegram nao encontrado." || exit /b 1
call :assert_file "%WEB_PANEL%" "Arquivo do painel web nao encontrado." || exit /b 1
call :assert_file "%GCV_AUTOMATION%" "Arquivo da automacao GCV nao encontrado." || exit /b 1

cd /d "%PROJECT_DIR%"
if errorlevel 1 (
    call :fail "Nao foi possivel acessar a pasta do projeto: %PROJECT_DIR%"
    exit /b 1
)

call :check_interactive_session || exit /b 1
call :check_gcv_dependencies || exit /b 1

if /I "%~1"=="--check" (
    echo.
    echo Validacao concluida com sucesso. Nenhuma automacao foi executada.
    exit /b 0
)

set "PAINEL_HOST=0.0.0.0"
set "PAINEL_PORT=5000"
set "PYTHONPATH=%BACKEND_SRC%;%PYTHONPATH%"

echo.
echo Iniciando backend, painel web e bot Telegram existentes...
echo Projeto: "%PROJECT_DIR%"
echo Python: "%PYTHON_BIN%"
echo.
echo A funcao GCV controla a tela somente durante a execucao do comando.
echo Mantenha a sessao do Windows desbloqueada enquanto a automacao estiver em andamento.
echo.

"%PYTHON_BIN%" "%BACKEND_MAIN%"
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo Backend finalizou com erro. Codigo: %EXIT_CODE%
    call :pause_if_needed
)

exit /b %EXIT_CODE%

:assert_dir
if exist "%~1\" exit /b 0
echo.
echo ERRO: %~2
echo Caminho: "%~1"
call :pause_if_needed
exit /b 1

:assert_file
if exist "%~1" exit /b 0
echo.
echo ERRO: %~2
echo Caminho: "%~1"
call :pause_if_needed
exit /b 1

:check_interactive_session
"%PYTHON_BIN%" -c "import ctypes, sys; sid=ctypes.c_ulong(); ok=ctypes.windll.kernel32.ProcessIdToSessionId(ctypes.windll.kernel32.GetCurrentProcessId(), ctypes.byref(sid)); sys.exit(1 if ok and sid.value == 0 else 0)"
if errorlevel 1 (
    echo.
    echo ERRO: Este backend precisa rodar na sessao interativa do Windows.
    echo Nao execute como servico, tarefa isolada na Session 0 ou outro usuario.
    echo A funcao GCV controla a tela somente durante a execucao do comando.
    echo Mantenha a sessao do Windows desbloqueada enquanto a automacao estiver em andamento.
    call :pause_if_needed
    exit /b 1
)
exit /b 0

:check_gcv_dependencies
set "DEPS_REPORT=%TEMP%\bot_gcv_deps_%RANDOM%%RANDOM%.txt"
"%PYTHON_BIN%" -c "import importlib.util, sys; mods=('pyautogui','pywinauto','cv2'); missing=[m for m in mods if importlib.util.find_spec(m) is None]; print(', '.join(missing)); sys.exit(1 if missing else 0)" > "%DEPS_REPORT%"
if errorlevel 1 (
    echo.
    echo ERRO: Dependencias GCV ausentes:
    type "%DEPS_REPORT%"
    echo.
    echo Execute o comando abaixo e abra este BAT novamente:
    echo .\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
    del "%DEPS_REPORT%" >nul 2>nul
    call :pause_if_needed
    exit /b 1
)
del "%DEPS_REPORT%" >nul 2>nul
exit /b 0

:fail
echo.
echo ERRO: %~1
call :pause_if_needed
exit /b 1

:pause_if_needed
if not defined BOT_BAT_NO_PAUSE pause
exit /b 0
