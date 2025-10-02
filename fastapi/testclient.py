from __future__ import annotations

from typing import Any, Dict, Optional

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
