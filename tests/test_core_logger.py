from __future__ import annotations

import logging
import sys
from types import SimpleNamespace

import pytest


class _DummyRichHandler:
    def __init__(self, rich_tracebacks: bool = False) -> None:
        self.rich_tracebacks = rich_tracebacks


_rich_logging = SimpleNamespace(RichHandler=_DummyRichHandler)
sys.modules.setdefault("rich", SimpleNamespace(logging=_rich_logging))
sys.modules.setdefault("rich.logging", _rich_logging)

from core import logger as core_logger


def test_get_logger_respects_environment_level(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_basic_config(**kwargs: object) -> None:
        captured.update(kwargs)

    monkeypatch.setenv("COMAN_LOG_LEVEL", "debug")
    monkeypatch.setattr(core_logger.logging, "basicConfig", fake_basic_config)

    log = core_logger.get_logger("integration-test")

    assert captured["level"] == "DEBUG"
    handlers = captured.get("handlers")
    assert handlers and any(isinstance(h, core_logger.RichHandler) for h in handlers)
    assert log.name == "integration-test"
