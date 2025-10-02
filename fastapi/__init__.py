"""Compatibility wrapper that prefers the real FastAPI package when available.

The repository vendors a very small FastAPI stub so the unit tests can run
without installing the full dependency tree.  When the application is executed
in a real environment, however, we want to use the actual ``fastapi`` package
installed in the interpreter.  Because this stub lives alongside the project
code it takes precedence on ``sys.path`` and masks the real dependency, which
breaks imports such as ``fastapi.Form``.

This module therefore tries to locate and load the external distribution first.
If that succeeds we expose it transparently; otherwise we fall back to the
lightweight stub so tests continue to function.
"""

from __future__ import annotations

import importlib
import importlib.machinery
import importlib.util
import os
import site
import sys
import sysconfig
from pathlib import Path
from types import ModuleType
from typing import Iterable


def _iter_site_packages() -> Iterable[str]:
    """Yield candidate directories that may contain installed packages."""

    seen: set[str] = set()

    for getter_name in ("getsitepackages", "getusersitepackages"):
        getter = getattr(site, getter_name, None)
        if getter is None:
            continue
        try:
            value = getter()
        except Exception:  # pragma: no cover - extremely defensive
            continue
        if isinstance(value, str):
            candidates = [value]
        else:
            candidates = list(value)
        for path in candidates:
            if path and path not in seen:
                seen.add(path)
                yield path

    for key in ("purelib", "platlib"):
        try:
            path = sysconfig.get_path(key)
        except KeyError:  # pragma: no cover - defensive
            continue
        if path and path not in seen:
            seen.add(path)
            yield path


def _load_real_fastapi() -> ModuleType | None:
    """Try to load the external FastAPI distribution if it is installed."""

    finder = importlib.machinery.PathFinder

    for root in _iter_site_packages():
        spec = finder.find_spec("fastapi", [root])
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules[__name__] = module
            spec.loader.exec_module(module)
            return module

    placeholder = sys.modules.pop(__name__, None)
    try:
        module = importlib.import_module("fastapi")
    except Exception:
        module = None
    finally:
        if placeholder is not None:
            sys.modules[__name__] = placeholder

    if module is not None:
        module_path = getattr(module, "__file__", None)
        if module_path and Path(module_path).resolve() != Path(__file__).resolve():
            return module

    return None


_real_fastapi: ModuleType | None = None

if os.environ.get("COMAN_USE_FASTAPI_STUB") != "1":
    _real_fastapi = _load_real_fastapi()

if _real_fastapi is not None:
    globals().update(_real_fastapi.__dict__)
    sys.modules[__name__] = _real_fastapi
else:
    from .app import FastAPI
    from .routing import APIRouter
    from .exceptions import HTTPException
    from .params import Body, File, Form, Query

    try:  # pragma: no cover - optional helper module
        from .responses import JSONResponse, StreamingResponse
    except Exception:  # pragma: no cover - minimal fallback
        JSONResponse = StreamingResponse = None  # type: ignore[assignment]

    class Request:  # pragma: no cover - lightweight placeholder
        def __init__(self, scope: dict | None = None):
            self.scope = scope or {}

    class UploadFile:  # pragma: no cover - lightweight placeholder
        def __init__(self, filename: str | None = None, file=None):
            import io

            self.filename = filename
            self.file = file or io.BytesIO()

        async def read(self) -> bytes:
            data = self.file.read()
            if hasattr(data, "__await__"):
                data = await data
            return data or b""

    __all__ = [
        "FastAPI",
        "APIRouter",
        "HTTPException",
        "Body",
        "File",
        "Form",
        "Query",
        "Request",
        "UploadFile",
    ]
    if JSONResponse is not None and StreamingResponse is not None:
        __all__.extend(["JSONResponse", "StreamingResponse"])
