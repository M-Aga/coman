# Coman Unified Platform ![Test coverage](docs/assets/coverage.svg)

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

* Python 3.12+
* [`uv`](https://docs.astral.sh/uv/latest/) for managing environments and running tasks
* Optional: ``uvicorn`` for serving the HTTP API (installed automatically when
  running the API service with the CLI instructions below)

## Quick start

1. **Install dependencies:**
    ```bash
    uv sync
    ```
    ``uv`` reads ``pyproject.toml`` and ``uv.lock`` to install both the runtime
    and development tooling in a local ``.venv`` automatically.
2. **Run one of the available services:**
    ```bash
    uv run python -m coman.modules.main [api|telegram|all|dual] [--host 0.0.0.0] [--port 8000] [--reload]
    ```
    * ``api`` – start the FastAPI core with every registered module
    * ``telegram`` – launch the Telegram bot runner
    * ``all``/``dual`` – run the HTTP API and Telegram bot together (API runs in a background thread)

Windows users can double click ``run_coman.bat`` (or execute it from PowerShell)
to run the same command; the script automatically prefers a local ``.venv``
interpreter when available.  Linux/macOS users can use the matching
``run_coman.sh`` helper which offers the same behaviour for POSIX shells.

## Development workflows

The repository provides a ``Makefile`` that proxies common tasks through ``uv``:

```bash
make format     # Ruff formatting
make lint       # Ruff lint checks
make typecheck  # mypy static analysis
make test       # pytest with coverage (fails below 85% for ``core``)
make coverage   # pytest + badge generation at docs/assets/coverage.svg
make run        # Launch the FastAPI application
```

``make sync`` is available as a shortcut for ``uv sync`` when bootstrapping a
fresh clone.

## Running the test-suite

```bash
make test       # quick feedback
make coverage   # refresh coverage badge
```

## Troubleshooting

* ``ModuleNotFoundError: No module named 'coman'`` – ensure you are running the
  commands from the project root *after* installing the package requirements.
  The new ``coman`` package exposes the existing ``core`` and ``modules``
  directories so importing ``coman.*`` works without additional monkey-patching.

* ``ModuleNotFoundError`` for ``fastapi``, ``pydantic``, ``apscheduler`` or
  ``telegram`` – ensure ``uv sync`` has been executed.  The repository exposes a
  ``telegram`` shim that forwards imports to the upstream
  ``python-telegram-bot`` package while keeping ``telegram.coman`` available,
  so the real SDK must be present in the environment.

* ``uvicorn`` import errors – add the web server with ``uv add uvicorn`` or run
  the API service via the CLI which will raise a helpful message if the
  dependency is missing.
