@echo off
cd /d "%~dp0"
setlocal
set "TESIS_ENV=%USERPROFILE%\anaconda3\envs\tesis-nlp313"
set "TESIS_PYTHON=%TESIS_ENV%\python.exe"
if not exist "%TESIS_PYTHON%" set "TESIS_PYTHON=python"
set "PATH=%TESIS_ENV%;%TESIS_ENV%\Library\bin;%TESIS_ENV%\Scripts;%PATH%"
set "PYTHONIOENCODING=utf-8"
set "PYTHONDONTWRITEBYTECODE=1"
set "HF_HUB_OFFLINE=1"
set "GRADIO_SERVER_PORT=7861"
set "TESIS_ABRIR_NAVEGADOR=1"
if not exist ".gradio\Scripts\python.exe" (
    "%TESIS_PYTHON%" -m venv --system-site-packages ".gradio"
    if errorlevel 1 exit /b 1
    ".gradio\Scripts\python.exe" -m pip install -r requirements-gradio.txt
    if errorlevel 1 exit /b 1
)
".gradio\Scripts\python.exe" -u aplicativo\app.py
set "RESULTADO=%ERRORLEVEL%"
pause
exit /b %RESULTADO%
