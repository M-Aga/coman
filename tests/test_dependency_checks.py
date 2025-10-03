import os
import types
from pathlib import Path

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


def _setup_fake_environment(path: Path) -> Path:
    scripts_dir = "Scripts" if os.name == "nt" else "bin"
    python_name = "python.exe" if os.name == "nt" else "python"
    bin_dir = path / scripts_dir
    bin_dir.mkdir(parents=True, exist_ok=True)
    python_path = bin_dir / python_name
    python_path.write_text("")
    return python_path


def test_create_virtual_environment_creates_and_installs(monkeypatch, tmp_path):
    from coman.modules import main

    env_dir = tmp_path / ".venv"
    requirements = tmp_path / "requirements.txt"
    requirements.write_text("httpx\n")

    created: dict[str, bool] = {"called": False}

    def fake_builder(**kwargs):
        class Dummy:
            def create(self, location: str) -> None:
                created["called"] = True
                _setup_fake_environment(Path(location))

        return Dummy()

    monkeypatch.setattr(main.venv, "EnvBuilder", fake_builder)

    commands: list[list[str]] = []

    def fake_check_call(cmd, **kwargs):
        commands.append(cmd)

    monkeypatch.setattr(main.subprocess, "check_call", fake_check_call)

    python_path = main.create_virtual_environment(env_dir, requirements, install_dependencies=True)

    assert created["called"] is True
    expected_python = main._venv_python_path(env_dir)
    assert python_path == expected_python
    assert commands == [[str(expected_python), "-m", "pip", "install", "-r", str(requirements)]]


def test_create_virtual_environment_missing_requirements(monkeypatch, tmp_path):
    from coman.modules import main

    env_dir = tmp_path / ".venv"

    def fake_builder(**kwargs):
        class Dummy:
            def create(self, location: str) -> None:
                _setup_fake_environment(Path(location))

        return Dummy()

    monkeypatch.setattr(main.venv, "EnvBuilder", fake_builder)

    called = False

    def fake_check_call(cmd, **kwargs):
        nonlocal called
        called = True

    monkeypatch.setattr(main.subprocess, "check_call", fake_check_call)

    missing_requirements = tmp_path / "missing.txt"
    python_path = main.create_virtual_environment(env_dir, missing_requirements, install_dependencies=True)

    assert python_path == main._venv_python_path(env_dir)
    assert called is False


def test_main_handles_venv_command(monkeypatch, tmp_path):
    from coman.modules import main

    captured: dict[str, tuple] = {}

    def fake_create(location, requirements, install_dependencies):
        captured["args"] = (location, requirements, install_dependencies)

    monkeypatch.setattr(main, "create_virtual_environment", fake_create)

    path = tmp_path / "env"
    requirements = tmp_path / "req.txt"

    main.main(
        [
            "venv",
            "--path",
            str(path),
            "--requirements",
            str(requirements),
            "--no-install",
        ]
    )

    assert captured["args"] == (str(path), str(requirements), False)
