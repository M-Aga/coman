from __future__ import annotations

import asyncio
import inspect
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Mapping

from fastapi import APIRouter


def _normalise_route_methods(route: Any) -> List[str]:
    methods: Iterable[str] | None = getattr(route, "methods", None)
    if not methods:
        method = getattr(route, "method", None)
        if method:
            methods = [method]
        else:
            methods = []
    return sorted({m.upper() for m in methods})


def _normalise_route_path(route: Any) -> str:
    path = getattr(route, "path", None)
    if not path:
        path = getattr(route, "path_format", "")
    return str(path or "")


def _is_fastapi_param(default: Any) -> bool:
    cls = default.__class__
    module = getattr(cls, "__module__", "")
    name = getattr(cls, "__name__", "")
    if module.startswith("fastapi"):
        return True
    return name in {"Body", "File", "Form", "Query", "Header", "Path"}


def _coerce_parameter_value(value: Any, annotation: Any) -> Any:
    if annotation is inspect._empty or value is None:
        return value
    origin = getattr(annotation, "__origin__", None)
    if origin in (list, List) and isinstance(value, str):
        try:
            import json

            parsed = json.loads(value)
        except Exception:
            return [value]
        if isinstance(parsed, list):
            return parsed
        return [parsed]
    if origin in (dict, Dict, Mapping) and isinstance(value, str):
        try:
            import json

            parsed = json.loads(value)
        except Exception:
            return value
        if isinstance(parsed, dict):
            return parsed
    return value


@dataclass
class ConsoleOperation:
    """Representation of a module endpoint that can be invoked from the CLI."""

    name: str
    route: Any
    endpoint: Callable[..., Any]

    def describe(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "path": _normalise_route_path(self.route),
            "methods": _normalise_route_methods(self.route),
            "summary": getattr(self.route, "summary", ""),
        }

    def invoke(self, arguments: Mapping[str, Any] | None = None) -> Any:
        arguments = dict(arguments or {})
        signature = inspect.signature(self.endpoint)
        bound: Dict[str, Any] = {}
        for name, parameter in signature.parameters.items():
            if name in arguments:
                value = arguments[name]
            elif parameter.default is not inspect._empty:
                default = parameter.default
                if _is_fastapi_param(default):
                    value = getattr(default, "default", None)
                else:
                    value = default
            else:
                raise TypeError(f"Missing required argument '{name}' for operation '{self.name}'")
            value = _coerce_parameter_value(value, parameter.annotation)
            bound[name] = value
        result = self.endpoint(**bound)
        if inspect.iscoroutine(result):  # pragma: no cover - async endpoints
            return asyncio.run(result)
        return result


class BaseModule:
    name: str = "base"
    version: str = "0.4.0"
    description: str = "Base module"

    def __init__(self, core: "Core"):
        self.core = core
        self.router = APIRouter(prefix=f"/{self.name}", tags=[self.name])

    def get_router(self):
        return self.router

    def register_schedules(self):
        pass

    # CLI helpers -----------------------------------------------------

    def _iter_console_routes(self) -> Iterable[Any]:
        routes = getattr(self.router, "routes", [])
        for route in routes:
            endpoint = getattr(route, "endpoint", None)
            if endpoint is None:
                continue
            yield route

    def _operation_keys(self, route: Any) -> List[str]:
        endpoint = getattr(route, "endpoint", None)
        keys: List[str] = []
        func_name = getattr(endpoint, "__name__", None)
        if func_name:
            keys.append(func_name)
        path = _normalise_route_path(route)
        if path:
            keys.append(path.lstrip("/"))
            keys.append(path.strip("/"))
        prefix = getattr(self.router, "prefix", "")
        if prefix and path.startswith(prefix):
            short = path[len(prefix) :].lstrip("/")
            if short:
                keys.append(short)
        return [k for k in keys if k]

    def get_console_operations(self) -> Dict[str, ConsoleOperation]:
        operations: Dict[str, ConsoleOperation] = {}
        for route in self._iter_console_routes():
            endpoint = getattr(route, "endpoint", None)
            if endpoint is None:
                continue
            base_name = getattr(endpoint, "__name__", None) or _normalise_route_path(route)
            base_name = base_name.strip("/") or self.name
            op = ConsoleOperation(name=base_name, route=route, endpoint=endpoint)
            for key in self._operation_keys(route):
                key = key.strip()
                if not key:
                    continue
                lower = key.lower()
                if lower in operations:
                    continue
                operations[lower] = op
        return operations

    def describe_console_operations(self) -> List[Dict[str, Any]]:
        descriptions: List[Dict[str, Any]] = []
        seen = set()
        for route in self._iter_console_routes():
            endpoint = getattr(route, "endpoint", None)
            if endpoint is None:
                continue
            op = ConsoleOperation(
                name=getattr(endpoint, "__name__", None) or _normalise_route_path(route).strip("/") or self.name,
                route=route,
                endpoint=endpoint,
            )
            desc = op.describe()
            key = (desc["path"], tuple(desc["methods"]))
            if key in seen:
                continue
            seen.add(key)
            descriptions.append(desc)
        return descriptions

    def invoke_console_operation(self, name: str, arguments: Mapping[str, Any] | None = None) -> Any:
        operations = self.get_console_operations()
        key = name.strip().lower()
        operation = operations.get(key)
        if operation is None:
            available = ", ".join(sorted(operations)) or "<none>"
            raise KeyError(f"Unknown operation '{name}'. Available operations: {available}")
        return operation.invoke(arguments)
