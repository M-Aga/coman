"""Lightweight stubs of the telegram package for unit tests."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, List, Sequence

__all__ = [
    "InlineKeyboardButton",
    "InlineKeyboardMarkup",
    "Update",
]


class InlineKeyboardButton:
    def __init__(self, text: str, callback_data: str | None = None):
        self.text = text
        self.callback_data = callback_data


class InlineKeyboardMarkup:
    def __init__(self, inline_keyboard: Sequence[Sequence[InlineKeyboardButton]]):
        rows: List[List[InlineKeyboardButton]] = []
        for row in inline_keyboard:
            rows.append(list(row))
        self.inline_keyboard = rows


class Update:
    def __init__(self, **kwargs: Any) -> None:  # pragma: no cover - not used in tests
        self.effective_user = kwargs.get("effective_user", SimpleNamespace(id=0, username=""))
        self.effective_message = kwargs.get("effective_message")
        self.effective_chat = kwargs.get("effective_chat")
        self.callback_query = kwargs.get("callback_query")
        self.message = kwargs.get("message")
