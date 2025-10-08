from __future__ import annotations

from types import TracebackType
from typing import Any, Dict, Optional, Self, Type

from .app import FastAPI
from .routing import Response


class TestClient:
    __test__ = False  # Prevent pytest from collecting this class as a test

    def __init__(self, app: FastAPI):
        self.app = app

    def post(self, path: str, *, params: Optional[Dict[str, Any]] = None, json: Any = None) -> Response:
        return self.app._handle_request("POST", path, params=params, json_body=json)

    def get(self, path: str, *, params: Optional[Dict[str, Any]] = None) -> Response:
        return self.app._handle_request("GET", path, params=params, json_body=None)

    # ------------------------------------------------------------------
    # Context manager plumbing to mirror the Starlette TestClient API.
    # The real TestClient integrates with a transport layer that needs to
    # be closed; our lightweight shim does not have external resources but
    # we keep the same public surface so ``with TestClient(app)`` works even
    # when the stub is used.  Returning ``self`` keeps usage identical to
    # ``starlette.testclient.TestClient``.
    # ------------------------------------------------------------------
    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: Type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool:
        self.close()
        return False

    def close(self) -> None:
        """Mirror the real TestClient interface."""
        return None

