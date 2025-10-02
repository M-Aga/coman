"""Unified entry point for running Coman services and module utilities."""

from __future__ import annotations

import argparse
import json
import logging
import sys
import threading
from contextlib import contextmanager
from typing import Any, Dict, Iterator, List

from coman.core.base_module import BaseModule
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


def _load_core() -> Core:
    core = Core()
    load_modules(core)
    return core


def run_api(host: str = "127.0.0.1", port: int = 8000, reload: bool = False) -> None:
    """Start the FastAPI application with all registered modules."""

    from coman.core.app import build_fastapi_app

    uvicorn = _import_uvicorn()
    core = _load_core()
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


def _describe_module(module: BaseModule) -> Dict[str, Any]:
    operations = module.describe_console_operations()
    return {
        "name": module.name,
        "description": module.description,
        "version": module.version,
        "operations": operations,
    }


def list_modules(as_json: bool = False) -> None:
    core = _load_core()
    modules_info: List[Dict[str, Any]] = []
    for module in core.modules.values():
        modules_info.append(_describe_module(module))

    if as_json:
        json.dump(modules_info, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return

    if not modules_info:
        print("No modules loaded")
        return

    name_width = max(len(info["name"]) for info in modules_info)
    for info in modules_info:
        print(f"{info['name']:<{name_width}}  {info['description']}")
        for op in info["operations"]:
            methods = ",".join(op.get("methods") or [])
            path = op.get("path", "")
            summary = op.get("summary", "")
            if methods:
                methods_display = f"[{methods}]"
            else:
                methods_display = ""
            print(f"    - {op['name']} {methods_display} {path} {summary}".rstrip())


def _parse_kv(arg: str) -> Dict[str, Any]:
    if "=" not in arg:
        raise SystemExit(f"Invalid argument '{arg}', expected key=value")
    key, value = arg.split("=", 1)
    key = key.strip()
    value = value.strip()
    if not key:
        raise SystemExit(f"Invalid argument '{arg}', key cannot be empty")
    try:
        value_obj = json.loads(value)
    except json.JSONDecodeError:
        value_obj = value
    return {key: value_obj}


def _merge_arguments(json_payload: str | None, args: List[str]) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    if json_payload:
        try:
            loaded = json.loads(json_payload)
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive guard
            raise SystemExit(f"Invalid JSON payload: {exc}") from exc
        if not isinstance(loaded, dict):
            raise SystemExit("JSON payload must be an object with key/value pairs")
        data.update(loaded)
    for item in args:
        data.update(_parse_kv(item))
    return data


def call_module(module_name: str, operation: str, json_payload: str | None, args: List[str]) -> None:
    core = _load_core()
    module = core.modules.get(module_name)
    if module is None:
        available = ", ".join(sorted(core.modules)) or "<none>"
        raise SystemExit(f"Unknown module '{module_name}'. Available modules: {available}")

    payload = _merge_arguments(json_payload, args)
    try:
        result = module.invoke_console_operation(operation, payload)
    except Exception as exc:
        raise SystemExit(f"Failed to execute {module_name}.{operation}: {exc}") from exc

    formatted = _format_result(result)
    if isinstance(formatted, str):
        print(formatted)
    else:
        json.dump(formatted, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")


def _format_result(result: Any) -> Any:
    if result is None:
        return {"ok": True}
    if hasattr(result, "to_payload"):
        try:
            return result.to_payload()
        except Exception:
            pass
    if hasattr(result, "model_dump"):
        try:
            return result.model_dump()
        except Exception:
            pass
    if hasattr(result, "dict"):
        try:
            return result.dict()  # type: ignore[call-arg]
        except Exception:
            pass
    if isinstance(result, (str, int, float, bool)):
        return result
    if isinstance(result, (list, dict)):
        return result
    return repr(result)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Coman services or interact with modules")
    subparsers = parser.add_subparsers(dest="command")

    serve = subparsers.add_parser("serve", help="Run API, Telegram bot, or both")
    serve.add_argument(
        "service",
        choices=("api", "telegram", "all"),
        default="api",
        nargs="?",
        help="Which service to run (default: api)",
    )
    serve.add_argument("--host", default="127.0.0.1", help="Host for the API server")
    serve.add_argument("--port", type=int, default=8000, help="Port for the API server")
    serve.add_argument("--reload", action="store_true", help="Enable auto-reload for the API server")
    serve.add_argument("--verbose", action="store_true", help="Enable debug logging")

    modules_cmd = subparsers.add_parser("modules", help="List available modules")
    modules_cmd.add_argument("--json", action="store_true", help="Output JSON instead of text")
    modules_cmd.add_argument("--verbose", action="store_true", help="Enable debug logging")

    call_cmd = subparsers.add_parser("call", help="Invoke a module operation without the API server")
    call_cmd.add_argument("module", help="Module name (e.g. analysis)")
    call_cmd.add_argument("operation", help="Operation name or route (e.g. frequency)")
    call_cmd.add_argument("--json", dest="payload", help="JSON payload with arguments")
    call_cmd.add_argument(
        "--arg",
        action="append",
        default=[],
        help="key=value argument (can be provided multiple times)",
    )
    call_cmd.add_argument("--verbose", action="store_true", help="Enable debug logging")

    return parser


def _parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    argv = list(argv or sys.argv[1:])
    if argv and argv[0] in {"api", "telegram", "all"}:
        argv = ["serve", *argv]
    parser = _build_parser()
    if not argv:
        argv = ["serve"]
    args = parser.parse_args(argv)
    return args


def main(argv: List[str] | None = None) -> None:
    args = _parse_args(argv)
    verbose = getattr(args, "verbose", False)
    _configure_logging(verbose)

    command = getattr(args, "command", "serve") or "serve"
    if command == "serve":
        service = getattr(args, "service", "api")
        if service == "api":
            run_api(args.host, args.port, args.reload)
        elif service == "telegram":
            run_telegram_bot()
        else:
            run_all(args.host, args.port, args.reload)
        return

    if command == "modules":
        list_modules(as_json=args.json)
        return

    if command == "call":
        call_module(args.module, args.operation, args.payload, args.arg)
        return

    raise SystemExit(f"Unknown command: {command}")


if __name__ == "__main__":  # pragma: no cover - CLI invocation
    main()
