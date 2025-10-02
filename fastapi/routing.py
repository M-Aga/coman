from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List


@dataclass
class Route:
    method: str
    path: str
    endpoint: Callable[..., Any]


class APIRouter:
    def __init__(self, prefix: str = "", tags: Iterable[str] | None = None):
        self.prefix = prefix.rstrip("/")
        if self.prefix and not self.prefix.startswith("/"):
            self.prefix = "/" + self.prefix
        self.tags = list(tags or [])
        self.routes: List[Route] = []

    def _full_path(self, path: str) -> str:
        path = path.strip()
        if not path.startswith("/"):
            path = "/" + path
        if self.prefix:
            if path == "/":
                return self.prefix or "/"
            return (self.prefix + path).replace("//", "/")
        return path

    def add_api_route(self, path: str, endpoint: Callable[..., Any], methods: Iterable[str]) -> Callable[..., Any]:
        full_path = self._full_path(path)
        for method in methods:
            self.routes.append(Route(method.upper(), full_path, endpoint))
        return endpoint

    def get(self, path: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return self.add_api_route(path, func, ["GET"])

        return decorator

    def post(self, path: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return self.add_api_route(path, func, ["POST"])

        return decorator


class Response:
    def __init__(self, status_code: int, json_data: Any):
        self.status_code = status_code
        self._json_data = json_data

    @property
    def text(self) -> str:
        import json

        if isinstance(self._json_data, (dict, list)):
            return json.dumps(self._json_data)
        return str(self._json_data)

    def json(self) -> Any:
        return self._json_data
