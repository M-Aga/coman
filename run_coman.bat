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

"%PYTHON%" -c "import importlib, sys;"^
    "missing = [];"^
    "for name in ['fastapi','pydantic','httpx','apscheduler']:"^
    "    try:"^
    "        importlib.import_module(name)"^
    "    except Exception:"^
    "        missing.append(name);"^
    "try:"^
    "    import telegram"^
    "except Exception:"^
    "    missing.append('python-telegram-bot');"^
    "if missing:"^
    "    print('[Coman] Missing dependencies: ' + ', '.join(missing));"^
    "    sys.exit(1)"
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
