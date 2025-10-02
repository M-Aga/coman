"""Bridge the upstream :mod:`python-telegram-bot` package with Coman's service modules.

The project historically bundled its Telegram bot implementation under the
``telegram.coman`` namespace which clashes with the upstream distribution's
module name.  This shim delegates attribute access to the real
``python-telegram-bot`` package (if installed) while keeping the additional
``telegram.coman`` modules importable for backwards compatibility.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType
from typing import List

__all__: List[str] = ["coman"]

_PACKAGE_DIR = Path(__file__).resolve().parent


def _candidate_paths() -> List[str]:
    paths: List[str] = []
    for entry in list(sys.path):
        try:
            resolved = Path(entry).resolve()
        except Exception:  # pragma: no cover - defensive
            continue
        if resolved == _PACKAGE_DIR:
            continue
        try:
            relative = _PACKAGE_DIR.is_relative_to(resolved)
        except AttributeError:  # Python < 3.9 compatibility
            try:
                _PACKAGE_DIR.relative_to(resolved)
            except ValueError:
                relative = False
            else:
                relative = True
        if relative:
            continue
        paths.append(entry)
    return paths


def _load_vendor() -> ModuleType:
    candidates = _candidate_paths()
    if not candidates:
        raise ModuleNotFoundError(
            "python-telegram-bot is required. Install it with 'pip install "
            "python-telegram-bot>=21.0.0,<22.0.0'."
        )

    original_path = list(sys.path)
    this_module = sys.modules[__name__]
    try:
        sys.modules.pop(__name__, None)
        sys.path = candidates + [p for p in original_path if p not in candidates]
        module = importlib.import_module(__name__)
    finally:
        sys.path = original_path
        sys.modules[__name__] = this_module

    return module


_vendor = _load_vendor()
sys.modules.setdefault(f"{__name__}._vendor", _vendor)

# Mirror exported attributes from the upstream package.
for key, value in _vendor.__dict__.items():
    if key in {"__name__", "__loader__", "__package__", "__spec__"}:
        continue
    if key == "__path__":
        continue
    if key not in globals():
        globals()[key] = value

if hasattr(_vendor, "__all__"):
    __all__ = sorted(set(__all__) | set(getattr(_vendor, "__all__", [])))

# Extend our search path so vendor submodules (telegram.ext, etc.) resolve.
if hasattr(_vendor, "__path__"):
    for entry in _vendor.__path__:
        if entry not in __path__:
            __path__.append(entry)

if hasattr(_vendor, "__spec__") and _vendor.__spec__ is not None:
    __spec__.submodule_search_locations = getattr(_vendor.__spec__, "submodule_search_locations", __path__)

# Import Coman's service namespace so ``telegram.coman`` remains available.
from . import coman  # noqa: E402  (import at end to avoid circular re-exports)

root = sys.modules.setdefault("telegram", sys.modules[__name__])
root.coman = coman
