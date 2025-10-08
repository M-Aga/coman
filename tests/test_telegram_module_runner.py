from __future__ import annotations

import asyncio
import importlib
import sys
import types

import pytest


class DummyUpdater:
    def __init__(self):
        self.started = False
        self.stopped = False

    def start_polling(self):  # pragma: no cover - trivial stub
        self.started = True

    def stop(self):  # pragma: no cover - trivial stub
        self.stopped = True


class DummyApplication:
    def __init__(self):
        self.initialized = False
        self.started = False
        self.stopped = False
        self.shutdown_called = False
        self.updater = DummyUpdater()

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


@pytest.fixture
def telegram_module(monkeypatch):
    telegram_stub = types.ModuleType("telegram")

    class Update:  # pragma: no cover - simple stub
        pass

    telegram_stub.Update = Update

    telegram_ext_stub = types.ModuleType("telegram.ext")
    telegram_ext_stub.Application = DummyApplication
    telegram_ext_stub.ApplicationBuilder = object
    telegram_ext_stub.CommandHandler = object
    telegram_ext_stub.CallbackQueryHandler = object
    telegram_ext_stub.MessageHandler = object
    telegram_ext_stub.filters = types.SimpleNamespace(TEXT=object(), COMMAND=object())

    monkeypatch.setitem(sys.modules, "telegram", telegram_stub)
    monkeypatch.setitem(sys.modules, "telegram.ext", telegram_ext_stub)

    original_module = sys.modules.pop("modules.telegram_module.module", None)
    module = importlib.import_module("modules.telegram_module.module")

    try:
        yield module
    finally:
        if original_module is not None:
            sys.modules["modules.telegram_module.module"] = original_module
        else:
            sys.modules.pop("modules.telegram_module.module", None)


@pytest.fixture(autouse=True)
def _settings(monkeypatch, telegram_module):
    monkeypatch.setattr(telegram_module.settings, "telegram_bot_token", "dummy-token", raising=False)
    monkeypatch.setattr(telegram_module.settings, "api_base", "http://example", raising=False)


def test_runner_builds_application(monkeypatch, telegram_module):
    captured_cfg = {}
    fake_app = DummyApplication()

    def fake_build_application(cfg):
        captured_cfg["token"] = cfg.telegram_token
        captured_cfg["api_base_url"] = cfg.api_base_url
        return fake_app

    monkeypatch.setattr(telegram_module, "build_application", fake_build_application)

    class DummyCore:
        pass

    mod = telegram_module.Module(DummyCore())
    mod._stop.set()

    mod._runner()

    assert captured_cfg == {"token": "dummy-token", "api_base_url": "http://example"}
    assert mod.app is fake_app
    assert fake_app.initialized is True
    assert fake_app.started is True
    assert fake_app.stopped is True
    assert fake_app.shutdown_called is True
    assert fake_app.updater.started is True
