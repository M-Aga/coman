# Coman Unified Platform

Coman is a modular assistant platform that bundles a FastAPI-powered core with a
collection of pluggable automation modules (Telegram bot, orchestration logic,
speech/text pipelines, and more).  The repository now exposes an installable
``coman`` package so the project can be started with standard Python tooling.

## Repository layout

```
coman/                 # Python package shim that exposes the legacy layout
core/                  # Core FastAPI application and shared domain models
modules/               # Feature modules registered with the core orchestrator
telegram/              # Stand-alone Telegram bot wiring (re-used by the CLI)
data/                  # Sample datasets and resources used by modules
run_coman.bat          # Windows helper that executes ``python -m coman.modules.main``
```

## Requirements

* Python 3.10+ (the automation modules currently target 3.10/3.11/3.12)
* ``pip`` / ``venv`` for managing environments
* Optional: ``uvicorn`` for serving the HTTP API (installed automatically when
  running the API service with the CLI instructions below)

## Quick start

1. **Create a virtual environment (recommended):**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
   ```
2. **Install dependencies:** the ``modules/requirements.txt`` file now bundles
   the core runtime packages (FastAPI, Pydantic, APScheduler, httpx, and the
   Telegram bot SDK) so a single install step prepares both the API and bot
   runners.
   ```bash
   pip install -r modules/requirements.txt uvicorn
   ```
3. **Run one of the available services:**
   ```bash
   python -m coman.modules.main [api|telegram|all] [--host 0.0.0.0] [--port 8000] [--reload]
   ```
   * ``api`` – start the FastAPI core with every registered module
   * ``telegram`` – launch the Telegram bot runner
   * ``all`` – run the HTTP API and Telegram bot together (API runs in a background thread)

Windows users can double click ``run_coman.bat`` (or execute it from PowerShell)
to run the same command; the script automatically prefers a local ``.venv``
interpreter when available.

## Running the test-suite

```bash
pytest
```

## Troubleshooting

* ``ModuleNotFoundError: No module named 'coman'`` – ensure you are running the
  commands from the project root *after* installing the package requirements.
  The new ``coman`` package exposes the existing ``core`` and ``modules``
  directories so importing ``coman.*`` works without additional monkey-patching.
* ``ModuleNotFoundError`` for ``fastapi``, ``pydantic``, ``apscheduler`` or
  ``telegram`` – install the runtime dependencies with
  ``pip install -r modules/requirements.txt``.  The repository exposes a
  ``telegram`` shim that forwards imports to the upstream
  ``python-telegram-bot`` package while keeping ``telegram.coman`` available,
  so the real SDK must be present in the environment.
* ``uvicorn`` import errors – install the web server with
  ``pip install uvicorn`` or run the API service via the CLI which will raise a
  helpful message if the dependency is missing.
