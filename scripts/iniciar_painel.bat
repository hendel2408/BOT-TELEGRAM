@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PROJECT_DIR=%%~fI"
set "PYTHON_BIN=%PROJECT_DIR%\venv\Scripts\python.exe"
set "BACKEND_DIR=%PROJECT_DIR%\backend"

if not exist "%PYTHON_BIN%" (
    echo Python do ambiente virtual nao encontrado em:
    echo %PYTHON_BIN%
    exit /b 1
)

if not exist "%BACKEND_DIR%\app.py" (
    echo Backend nao encontrado em:
    echo %BACKEND_DIR%
    exit /b 1
)

cd /d "%PROJECT_DIR%"
set "PAINEL_HOST=0.0.0.0"
set "PAINEL_PORT=5000"

"%PYTHON_BIN%" "%BACKEND_DIR%\app.py"
