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

%PYTHON% -m coman.modules.main %*
set EXIT_CODE=%ERRORLEVEL%

popd

exit /b %EXIT_CODE%
