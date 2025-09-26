"""Unified entry point for running Coman services.

This CLI makes it easy to run the FastAPI core, the Telegram bot,
 or both at the same time.  Previously the module only proxied the
 Telegram runner, which meant other components had to be launched
 manually from separate scripts.  Consolidating the logic here lets
 contributors keep behaviour in sync across the different branches
 of the project.
"""

from __future__ import annotations

import argparse
import logging
import threading
from contextlib import contextmanager
from typing import Iterator

from coman.core.app import build_fastapi_app
from coman.core.registry import Core, load_modules


log = logging.getLogger("coman.main")


def _import_uvicorn():
    try:
        import uvicorn  # type: ignore
    except Exception as exc:  # pragma: no cover - defensive guard
        raise SystemExit(
            "uvicorn is required to run the API server. Install it with 'pip install uvicorn'"
        ) from exc
    return uvicorn


def _configure_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def run_api(host: str = "127.0.0.1", port: int = 8000, reload: bool = False) -> None:
    """Start the FastAPI application with all registered modules."""

    uvicorn = _import_uvicorn()
    core = Core()
    load_modules(core)
    app = build_fastapi_app(core)
    log.info("Starting FastAPI core on %s:%s", host, port)
    uvicorn.run(app, host=host, port=port, reload=reload)  # pragma: no cover - network server


def run_telegram_bot() -> None:
    """Launch the Telegram bot helper."""

    from coman.modules.telegram_module.bot import run as run_bot

    log.info("Starting Telegram bot")
    run_bot()


@contextmanager
def _background_thread(target, *args, **kwargs) -> Iterator[threading.Thread]:
    thread = threading.Thread(target=target, args=args, kwargs=kwargs, daemon=True)
    thread.start()
    try:
        yield thread
    finally:
        if thread.is_alive():
            log.info("Background thread %s is still running", thread.name)


def run_all(host: str = "127.0.0.1", port: int = 8000, reload: bool = False) -> None:
    """Run both the FastAPI server and the Telegram bot together."""

    with _background_thread(run_api, host, port, reload):
        run_telegram_bot()


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Coman services")
    parser.add_argument(
        "service",
        choices=("api", "telegram", "all"),
        default="api",
        nargs="?",
        help="Which service to run (default: api)",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host for the API server")
    parser.add_argument("--port", type=int, default=8000, help="Port for the API server")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for the API server")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    _configure_logging(args.verbose)

    if args.service == "api":
        run_api(args.host, args.port, args.reload)
    elif args.service == "telegram":
        run_telegram_bot()
    else:
        run_all(args.host, args.port, args.reload)


if __name__ == "__main__":  # pragma: no cover - CLI invocation
    main()
