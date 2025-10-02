from __future__ import annotations

from typing import Any, Dict, Iterable

from .exceptions import HTTPException
from .params import _Body
from .routing import APIRouter, Response, Route


class FastAPI:
    def __init__(self) -> None:
        self._routes: list[Route] = []

    def include_router(self, router: APIRouter) -> None:
        self._routes.extend(router.routes)

    def add_api_route(self, path: str, endpoint, methods: Iterable[str]) -> None:
        router = APIRouter()
        router.add_api_route(path, endpoint, methods)
        self.include_router(router)

    def _match_route(self, method: str, path: str) -> Route | None:
        for route in self._routes:
            if route.method == method and route.path == path:
                return route
        return None

    def _handle_request(self, method: str, path: str, params: Dict[str, Any] | None, json_body: Any) -> Response:
        route = self._match_route(method, path)
        if route is None:
            return Response(status_code=404, json_data={"detail": "Not Found"})

        call_kwargs: Dict[str, Any] = {}
        if params:
            call_kwargs.update(params)
        if isinstance(json_body, dict):
            for key, value in json_body.items():
                call_kwargs.setdefault(key, value)

        signature = None
        try:
            import inspect

            signature = inspect.signature(route.endpoint)
        except (TypeError, ValueError):  # pragma: no cover
            signature = None

        if signature is not None:
            bound_defaults = {}
            for name, parameter in signature.parameters.items():
                default = parameter.default
                if isinstance(default, _Body):
                    default = default.default
                if default is not inspect._empty:  # type: ignore[attr-defined]
                    bound_defaults[name] = default
            for name, default in bound_defaults.items():
                call_kwargs.setdefault(name, default)

        try:
            result = route.endpoint(**call_kwargs)
        except HTTPException as exc:
            return Response(status_code=exc.status_code, json_data={"detail": exc.detail})

        return Response(status_code=200, json_data=result)
