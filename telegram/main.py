"""Compatibility wrapper to launch the Telegram bot.

Historically the Telegram distribution shipped its own ``main.py``.
The unified CLI in :mod:`coman.modules.main` now provides the same
behaviour, so this thin wrapper keeps existing commands working.
"""

from coman.modules.main import run_telegram_bot


if __name__ == "__main__":  # pragma: no cover - CLI invocation
    run_telegram_bot()
