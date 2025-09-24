import sys
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import core  # noqa: E402
import modules  # noqa: E402


pkg = types.ModuleType("coman")
pkg.__path__ = [str(ROOT)]
pkg.core = core
pkg.modules = modules


sys.modules.setdefault("coman", pkg)
sys.modules.setdefault("coman.core", core)
sys.modules.setdefault("coman.modules", modules)
