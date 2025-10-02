"""Bridge module that exposes the legacy :mod:`modules` package under ``coman.modules``."""
from __future__ import annotations

import sys
from importlib import import_module
from pathlib import Path
from types import ModuleType
from typing import Iterable

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_modules_pkg = import_module("modules")

__all__ = getattr(_modules_pkg, "__all__", [])  # type: ignore[var-annotated]
__path__ = getattr(_modules_pkg, "__path__", [])  # type: ignore[var-annotated]

if __spec__ is not None and getattr(_modules_pkg, "__spec__", None) is not None:
    __spec__.submodule_search_locations = getattr(
        _modules_pkg.__spec__, "submodule_search_locations", __path__
    )


def __getattr__(name: str):
    return getattr(_modules_pkg, name)


def __dir__() -> Iterable[str]:
    return sorted(set(__all__) | set(dir(_modules_pkg)))


def _register_submodules() -> None:
    for attribute in dir(_modules_pkg):
        obj = getattr(_modules_pkg, attribute)
        if isinstance(obj, ModuleType):
            sys.modules.setdefault(f"{__name__}.{attribute}", obj)


_register_submodules()
