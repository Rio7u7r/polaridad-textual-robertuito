@echo off
cd /d "%~dp0"
setlocal
set "TESIS_PYTHON=%USERPROFILE%\anaconda3\envs\tesis-nlp313\python.exe"
if not exist "%TESIS_PYTHON%" set "TESIS_PYTHON=python"
set "TESIS_ENV=%USERPROFILE%\anaconda3\envs\tesis-nlp313"
set "PATH=%TESIS_ENV%;%TESIS_ENV%\Library\bin;%TESIS_ENV%\Scripts;%PATH%"
set "PYTHONIOENCODING=utf-8"
set "PYTHONDONTWRITEBYTECODE=1"
"%TESIS_PYTHON%" -u ejecutar_cuadernos.py
set "RESULTADO=%ERRORLEVEL%"
pause
exit /b %RESULTADO%
