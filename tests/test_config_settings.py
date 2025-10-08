from __future__ import annotations

from pathlib import Path

import pytest

from core import config


def test_split_paths_normalises_and_deduplicates(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    raw = " ./one , /tmp/two , ./one , ./THREE "
    expected = {
        str((tmp_path / "one").resolve()),
        "/tmp/two",
        str((tmp_path / "THREE").resolve()),
    }
    result = config._split_paths(raw)
    assert len(result) == len(set(result))
    assert expected.issubset(set(result))


def test_split_paths_defaults_to_project_locations(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    result = config._split_paths("")
    cwd = str(tmp_path.resolve())
    assert result[0] == cwd
    expected_second = str((tmp_path / "integrations").resolve())
    assert expected_second in result
    assert len(result) == 2


def test_settings_stores_and_clears_token(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COMAN_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    settings = config.Settings()

    settings.store_telegram_bot_token("  secret  ")
    token_file = tmp_path / "telegram_token.txt"
    assert token_file.read_text(encoding="utf-8") == "secret"
    assert settings.telegram_bot_token == "secret"
    assert settings.telegram_token_source == "file"

    settings.store_telegram_bot_token("")
    assert not token_file.exists()
    assert settings.telegram_bot_token == ""
    assert settings.telegram_token_source == "none"


def test_settings_prefers_environment_token(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COMAN_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "from-env")
    settings = config.Settings()

    settings.store_telegram_bot_token("")
    assert settings.telegram_bot_token == "from-env"
    assert settings.telegram_token_source == "env"
