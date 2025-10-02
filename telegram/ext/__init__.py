"""Minimal telegram.ext stubs used in tests."""

from __future__ import annotations


class _DummyContext(dict):
    pass


class ContextTypes:
    DEFAULT_TYPE = _DummyContext


__all__ = ["ContextTypes"]
