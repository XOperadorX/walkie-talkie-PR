@echo off
cd /d "%~dp0"
python servidor\servidor_walkie.py
if errorlevel 1 (
  echo.
  echo O servidor foi encerrado com erro. Confira se o Python esta instalado.
  pause
)
