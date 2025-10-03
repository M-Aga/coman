from __future__ import annotations

import asyncio
import importlib
import sys
from types import ModuleType


class _DummyFilter:
    def __and__(self, _other):
        return self

    def __invert__(self):
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
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    class _DummyContextTypes:
        DEFAULT_TYPE = object()

    filters_stub = ModuleType("telegram.ext.filters")
    filters_stub.TEXT = _DummyFilter()
    filters_stub.COMMAND = _DummyFilter()

    ext_stub.Application = type("Application", (), {})
    ext_stub.ApplicationBuilder = type("ApplicationBuilder", (), {})
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


class FakeApplication:
    def __init__(self):
        self.handlers = []

    def add_handler(self, handler):  # pragma: no cover - trivial passthrough
        self.handlers.append(handler)

    async def initialize(self):
        await asyncio.sleep(0)

    async def start(self):
        await asyncio.sleep(0)

    async def stop(self):
        await asyncio.sleep(0)

    async def shutdown(self):
        await asyncio.sleep(0)


def test_runner_builds_application(monkeypatch):
    fake_app = FakeApplication()
    captured = {}

    class FakeBuilder:
        def __init__(self):
            captured["init"] = True

        def token(self, token):
            captured["token"] = token
            return self

        def build(self):
            captured["built"] = True
            return fake_app

    monkeypatch.setattr(telegram_module, "ApplicationBuilder", FakeBuilder)
    monkeypatch.setattr(telegram_module.settings, "telegram_bot_token", "TEST_TOKEN")

    mod = telegram_module.Module(DummyCore())
    mod._stop.set()

    mod._runner()

    assert captured == {"init": True, "token": "TEST_TOKEN", "built": True}
    assert mod.app is fake_app
