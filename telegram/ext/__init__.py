"""Minimal :mod:`telegram.ext` compatibility layer.

This project only needs a *very* small subset of the real
``python-telegram-bot`` package in order to run its Telegram module.  The
dependency is optional, so when it is not installed we provide a handful of
lightweight stand-ins that mimic the public API that our code interacts with.

Historically this module only exposed :class:`ContextTypes`, but recent changes
to the Telegram integration started importing :class:`Application`,
:class:`ApplicationBuilder`, :class:`MessageHandler` and ``filters`` as well.
The stub was not updated which meant importing the module crashed with
``cannot import name 'Application'``.  Loading modules should degrade
gracefully when Telegram support is unavailable, therefore we ship the
missing pieces here.
"""

from __future__ import annotations

from typing import Any, Callable


class _DummyContext(dict):
    """Very small mapping used as the default context type."""


class ContextTypes:
    DEFAULT_TYPE = _DummyContext


class Application:
    """Minimal asynchronous lifecycle used by the module runner tests."""

    def __init__(self) -> None:
        self.handlers: list[Any] = []

    def add_handler(self, handler: Any) -> None:  # pragma: no cover - trivial
        self.handlers.append(handler)

    async def initialize(self) -> None:  # pragma: no cover - asynchronous stub
        return None

    async def start(self) -> None:  # pragma: no cover - asynchronous stub
        return None

    async def stop(self) -> None:  # pragma: no cover - asynchronous stub
        return None

    async def shutdown(self) -> None:  # pragma: no cover - asynchronous stub
        return None


class ApplicationBuilder:
    """Fluent builder that mirrors the python-telegram-bot interface."""

    def __init__(self) -> None:
        self._token: str | None = None
        self._factory: Callable[[], Application] = Application

    def token(self, token: str) -> "ApplicationBuilder":
        self._token = token
        return self

    def build(self) -> Application:
        return self._factory()


class MessageHandler:
    """Container that stores handler configuration for tests."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.args = args
        self.kwargs = kwargs


class _Filter:
    def __and__(self, _other: Any) -> "_Filter":  # pragma: no cover - trivial
        return self

    def __invert__(self) -> "_Filter":  # pragma: no cover - trivial
        return self


class _FiltersModule:
    TEXT = _Filter()
    COMMAND = _Filter()


filters = _FiltersModule()


__all__ = [
    "Application",
    "ApplicationBuilder",
    "ContextTypes",
    "MessageHandler",
    "filters",
]
