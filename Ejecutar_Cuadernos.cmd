@echo off
cd /d "%~dp0"
setlocal
set "PYTHONIOENCODING=utf-8"
set "TOKENIZERS_PARALLELISM=false"
set "TESIS_ABRIR_NAVEGADOR=1"
call conda run --no-capture-output -n tesis-robertuito python -u ejecutar_cuadernos.py
pause
