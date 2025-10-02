@echo off
REM Entry point for launching Coman services on Windows.
REM Falls back to the global python if no virtual environment is found.

setlocal enableextensions enabledelayedexpansion

set SCRIPT_DIR=%~dp0
pushd "%SCRIPT_DIR%"

set PYTHON=python
if exist .venv\Scripts\python.exe (
    set PYTHON=.venv\Scripts\python.exe
)


set EXIT_CODE=0

"%PYTHON%" -c "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('apscheduler') else 1)" >nul 2>&1
if errorlevel 1 (
    echo.
    echo [Coman] Missing required dependency 'apscheduler'.
    echo [Coman] Please run: pip install -r modules\requirements.txt
    set EXIT_CODE=1
    goto cleanup
)

"%PYTHON%" -m coman.modules.main %*
set EXIT_CODE=%ERRORLEVEL%


:cleanup
popd

exit /b %EXIT_CODE%
