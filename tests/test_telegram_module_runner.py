from __future__ import annotations

import importlib
import sys
import types

import pytest


class DummyApplication:
    def __init__(self):
        self.handlers = []
        self.initialized = False
        self.started = False
        self.stopped = False
        self.shutdown_called = False

    def add_handler(self, handler):
        self.handlers.append(handler)

    async def initialize(self):
        self.initialized = True

    async def start(self):
        self.started = True

    async def stop(self):
        self.stopped = True

    async def shutdown(self):
        self.shutdown_called = True


class DummyBuilder:
    def __init__(self):
        self.token_value = None

    def token(self, token):
        self.token_value = token
        return self

    def build(self):
        return DummyApplication()


class DummyMessageHandler:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class DummyFilters:
    TEXT = 1
    COMMAND = 2


class DummyContextTypes:
    DEFAULT_TYPE = object


@pytest.fixture
def telegram_module(monkeypatch):
    telegram_stub = types.ModuleType("telegram")

    class Update:  # pragma: no cover - simple stub
        pass

    telegram_stub.Update = Update

    telegram_ext_stub = types.ModuleType("telegram.ext")
    telegram_ext_stub.Application = DummyApplication
    telegram_ext_stub.ApplicationBuilder = DummyBuilder
    telegram_ext_stub.MessageHandler = DummyMessageHandler
    telegram_ext_stub.filters = DummyFilters
    telegram_ext_stub.ContextTypes = DummyContextTypes

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
    builders: list[DummyBuilder] = []
    apps: list[DummyApplication] = []

    def fake_builder():
        builder = DummyBuilder()
        builders.append(builder)

        original_build = builder.build

        def build_and_track():
            app = original_build()
            apps.append(app)
            return app

        builder.build = build_and_track
        return builder

    monkeypatch.setattr(telegram_module, "ApplicationBuilder", fake_builder)
    monkeypatch.setattr(telegram_module, "MessageHandler", DummyMessageHandler)
    monkeypatch.setattr(telegram_module, "filters", DummyFilters)

    class DummyCore:
        pass

    mod = telegram_module.Module(DummyCore())
    mod._stop.set()

    mod._runner()

    assert apps, "Application was not constructed"
    assert mod.app is apps[0]
    assert builders[0].token_value == "dummy-token"
