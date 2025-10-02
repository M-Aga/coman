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

"%PYTHON%" -c "import importlib, sys\nmissing = []\nfor name in ['fastapi','pydantic','httpx','apscheduler']:\n    try:\n        importlib.import_module(name)\n    except Exception:\n        missing.append(name)\ntry:\n    import telegram  # ensure python-telegram-bot is installed\nexcept Exception:\n    missing.append('python-telegram-bot')\nif missing:\n    print('[Coman] Missing dependencies: ' + ', '.join(missing))\n    sys.exit(1)\n"
if errorlevel 1 (
    echo [Coman] Install the required packages with:
    echo [Coman]     pip install -r modules\requirements.txt
    set EXIT_CODE=1
    goto cleanup
)

"%PYTHON%" -m coman.modules.main %*
set EXIT_CODE=%ERRORLEVEL%

:cleanup

popd

exit /b %EXIT_CODE%
