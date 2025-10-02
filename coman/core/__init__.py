"""Bridge module that exposes the legacy :mod:`core` package under ``coman.core``."""
from __future__ import annotations

import sys
from importlib import import_module
from pathlib import Path
from types import ModuleType
from typing import Iterable

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_core = import_module("core")

__all__ = getattr(_core, "__all__", [])  # type: ignore[var-annotated]
__path__ = getattr(_core, "__path__", [])  # type: ignore[var-annotated]

if __spec__ is not None and getattr(_core, "__spec__", None) is not None:
    __spec__.submodule_search_locations = getattr(_core.__spec__, "submodule_search_locations", __path__)


def __getattr__(name: str):
    return getattr(_core, name)


def __dir__() -> Iterable[str]:
    return sorted(set(__all__) | set(dir(_core)))


def _register_submodules() -> None:
    for attribute in dir(_core):
        obj = getattr(_core, attribute)
        if isinstance(obj, ModuleType):
            sys.modules.setdefault(f"{__name__}.{attribute}", obj)


_register_submodules()
