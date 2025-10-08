from __future__ import annotations

import asyncio
import importlib
import sys
from types import ModuleType


class _DummyFilter:
    def __and__(self, _other):  # pragma: no cover - trivial stub
        return self

    def __invert__(self):  # pragma: no cover - trivial stub
        return self


def _install_telegram_stubs() -> None:
    module = sys.modules.get("telegram")
    if module is None:
        try:  # Prefer the real implementation when available.
            module = importlib.import_module("telegram")
        except Exception:
            module = None

    if module is not None:
        try:
            ext_module = importlib.import_module("telegram.ext")
        except Exception:
            ext_module = None
        else:
            if hasattr(ext_module, "Application") and hasattr(ext_module, "ApplicationBuilder"):
                return

    telegram_stub = ModuleType("telegram")
    telegram_stub.Update = object  # type: ignore[attr-defined]

    ext_stub = ModuleType("telegram.ext")

    class _DummyMessageHandler:
        def __init__(self, *args, **kwargs):  # pragma: no cover - trivial stub
            self.args = args
            self.kwargs = kwargs

    class _DummyContextTypes:
        DEFAULT_TYPE = object()

    filters_stub = ModuleType("telegram.ext.filters")
    filters_stub.TEXT = _DummyFilter()
    filters_stub.COMMAND = _DummyFilter()

    ext_stub.Application = type("Application", (), {})
    ext_stub.ApplicationBuilder = type("ApplicationBuilder", (), {})
    ext_stub.CommandHandler = type("CommandHandler", (), {})
    ext_stub.CallbackQueryHandler = type("CallbackQueryHandler", (), {})
    ext_stub.MessageHandler = _DummyMessageHandler
    ext_stub.filters = filters_stub
    ext_stub.ContextTypes = _DummyContextTypes

    sys.modules["telegram"] = telegram_stub
    sys.modules["telegram.ext"] = ext_stub
    sys.modules["telegram.ext.filters"] = filters_stub


_install_telegram_stubs()

from modules.telegram_module import module as telegram_module


class DummyCore:
    """Minimal core stub required for Module initialisation."""


class FakeUpdater:
    def __init__(self):
        self.started = False
        self.stopped = False

    def start_polling(self):  # pragma: no cover - trivial stub
        self.started = True

    def stop(self):  # pragma: no cover - trivial stub
        self.stopped = True


class FakeApplication:
    def __init__(self):
        self.initialized = False
        self.started = False
        self.stopped = False
        self.shutdown_called = False
        self.updater = FakeUpdater()

    async def initialize(self):
        self.initialized = True
        await asyncio.sleep(0)

    async def start(self):
        self.started = True
        await asyncio.sleep(0)

    async def stop(self):
        self.stopped = True
        await asyncio.sleep(0)

    async def shutdown(self):
        self.shutdown_called = True
        await asyncio.sleep(0)


def test_runner_builds_application(monkeypatch):
    fake_app = FakeApplication()
    captured = {}

    def fake_build_application(cfg):
        captured["token"] = cfg.telegram_token
        captured["api_base_url"] = cfg.api_base_url
        return fake_app

    monkeypatch.setattr(telegram_module, "build_application", fake_build_application)
    monkeypatch.setattr(telegram_module.settings, "telegram_bot_token", "TEST_TOKEN")
    monkeypatch.setattr(telegram_module.settings, "api_base", "http://example")

    mod = telegram_module.Module(DummyCore())
    mod._stop.set()

    mod._runner()

    assert captured == {"token": "TEST_TOKEN", "api_base_url": "http://example"}
    assert mod.app is fake_app
    assert fake_app.updater.started is True
    assert fake_app.stopped is True
