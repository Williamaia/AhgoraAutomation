@echo off
setlocal
cd /d "%~dp0"
set PLAYWRIGHT_BROWSERS_PATH=0

if not exist ".venv\Scripts\python.exe" (
    echo Criando ambiente virtual...
    python -m venv .venv
)

echo Instalando dependencias...
".venv\Scripts\pip.exe" install -r requirements.txt

echo Instalando navegador Chromium...
".venv\Scripts\playwright.exe" install chromium

echo.
echo Setup concluido. Use:
echo   login.bat
echo   bater_ponto.bat
echo   bater_mes.bat
