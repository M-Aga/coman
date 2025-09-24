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


TELEGRAM_ROOT = ROOT / "telegram"
if TELEGRAM_ROOT.exists():
    try:
        import telegram as telegram_pkg  # type: ignore[import]
    except ImportError:
        telegram_pkg = types.ModuleType("telegram")
        telegram_pkg.__path__ = [str(TELEGRAM_ROOT)]
        sys.modules.setdefault("telegram", telegram_pkg)
    else:
        if hasattr(telegram_pkg, "__path__") and str(TELEGRAM_ROOT) not in telegram_pkg.__path__:
            telegram_pkg.__path__.append(str(TELEGRAM_ROOT))

    tg_coman = types.ModuleType("telegram.coman")
    tg_coman.__path__ = [str(TELEGRAM_ROOT / "coman")]
    tg_modules = types.ModuleType("telegram.coman.modules")
    tg_modules.__path__ = [str(TELEGRAM_ROOT / "coman" / "modules")]

    sys.modules.setdefault("telegram.coman", tg_coman)
    sys.modules.setdefault("telegram.coman.modules", tg_modules)

    setattr(telegram_pkg, "coman", tg_coman)
    setattr(tg_coman, "modules", tg_modules)
