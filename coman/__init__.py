"""Official Python package for the Coman unified assistant."""
from __future__ import annotations

import sys
from importlib import import_module
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

core = import_module("coman.core")
modules = import_module("coman.modules")

__all__ = ["core", "modules"]
