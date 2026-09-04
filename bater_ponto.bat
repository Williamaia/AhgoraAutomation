@echo off
setlocal
cd /d "%~dp0"
set PLAYWRIGHT_BROWSERS_PATH=0
".venv\Scripts\python.exe" scripts\bater_ponto.py %*
