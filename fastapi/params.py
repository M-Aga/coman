from dataclasses import dataclass
from typing import Any


@dataclass
class _Param:
    default: Any = None


def Body(default: Any = None, **_: Any) -> Any:
    """Return a sentinel used purely for default argument inspection."""
    return _Param(default)


_Body = _Param  # Backwards compatibility for modules importing the private name


def Query(default: Any = None, **_: Any) -> Any:
    return _Param(default)


def Form(default: Any = None, **_: Any) -> Any:
    return _Param(default)


def File(default: Any = None, **_: Any) -> Any:
    return _Param(default)
