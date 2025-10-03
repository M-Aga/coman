import types

import pytest


def _fake_import_factory(missing: set[str]):
    def _fake_import(name: str) -> types.ModuleType:
        if name in missing:
            raise ModuleNotFoundError(name)
        return types.ModuleType(name)

    return _fake_import


def test_ensure_runtime_dependencies_pass(monkeypatch):
    from coman.modules.main import ensure_runtime_dependencies

    monkeypatch.setattr(
        "coman.modules.main.import_module",
        _fake_import_factory(set()),
    )

    # Should not raise when all dependencies are available.
    ensure_runtime_dependencies({"api", "telegram"})


def test_ensure_runtime_dependencies_missing(monkeypatch):
    from coman.modules.main import ensure_runtime_dependencies

    missing = {"fastapi", "telegram"}
    monkeypatch.setattr(
        "coman.modules.main.import_module",
        _fake_import_factory(missing),
    )

    with pytest.raises(SystemExit) as exc:
        ensure_runtime_dependencies({"api", "telegram"})

    message = str(exc.value)
    assert "fastapi" in message
    assert "python-telegram-bot" in message
    assert "pip install -r modules/requirements.txt" in message
