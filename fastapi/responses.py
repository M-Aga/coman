from __future__ import annotations

from typing import Any, Iterable


class JSONResponse:
    """Minimal stub used for tests when FastAPI isn't installed."""

    def __init__(self, content: Any, status_code: int = 200):
        self.content = content
        self.status_code = status_code

    def json(self) -> Any:
        return self.content

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"JSONResponse(status_code={self.status_code}, content={self.content!r})"


class StreamingResponse:
    """Stub implementation that stores the iterator and metadata."""

    def __init__(
        self,
        content: Iterable[bytes] | bytes,
        media_type: str = "application/octet-stream",
        status_code: int = 200,
    ) -> None:
        self.content = content
        self.media_type = media_type
        self.status_code = status_code

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return (
            f"StreamingResponse(status_code={self.status_code}, media_type={self.media_type!r}, "
            f"content={self.content!r})"
        )
