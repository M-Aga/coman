from dataclasses import dataclass
from typing import Any


@dataclass
class _Body:
    default: Any = None


def Body(default: Any = None, **_: Any) -> Any:
    """Return a sentinel used purely for default argument inspection."""
    return _Body(default)
