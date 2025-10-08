from __future__ import annotations

import types

import pytest

from core import registry
from core.base_module import BaseModule


class DummyModule(BaseModule):
    name = "dummy"

    def __init__(self, core: registry.Core):
        super().__init__(core)


def test_load_modules_registers_discovered_packages(monkeypatch: pytest.MonkeyPatch) -> None:
    core = registry.Core()

    dummy_package = types.SimpleNamespace(__path__=[], __name__="coman.modules")

    def fake_import(name: str):
        if name == "coman.modules":
            return dummy_package
        return types.SimpleNamespace(Module=DummyModule)

    monkeypatch.setattr(registry.importlib, "import_module", fake_import)

    def fake_iter_modules(path, prefix):
        assert prefix == "coman.modules."
        return [types.SimpleNamespace(name="coman.modules.dummy", ispkg=True)]

    monkeypatch.setattr(registry.pkgutil, "iter_modules", lambda *args, **kwargs: fake_iter_modules(*args, **kwargs))

    registry.load_modules(core)
    assert "dummy" in core.modules
    assert isinstance(core.modules["dummy"], DummyModule)


def test_load_modules_skips_packages_without_module(monkeypatch: pytest.MonkeyPatch) -> None:
    core = registry.Core()

    monkeypatch.setattr(registry.importlib, "import_module", lambda name: types.SimpleNamespace() if name != "coman.modules" else types.SimpleNamespace(__path__=[], __name__="coman.modules"))

    monkeypatch.setattr(
        registry.pkgutil,
        "iter_modules",
        lambda *args, **kwargs: [types.SimpleNamespace(name="coman.modules.empty", ispkg=True)],
    )

    registry.load_modules(core)
    assert core.modules == {}
