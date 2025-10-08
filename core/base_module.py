from __future__ import annotations

import asyncio
import inspect
from contextlib import nullcontext
from dataclasses import dataclass
from datetime import date
from typing import Any, Callable, Dict, Iterable, List, Mapping

from fastapi import APIRouter

from observability import setup_module_observability
from coman.version import (
    API_MAJOR_VERSION,
    LEGACY_ROUTE_REMOVAL_DATE,
    get_module_version,
)
from opentelemetry.trace import Tracer


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
    module_name: str
    tracer: Tracer | None = None

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
        span_context = (
            self.tracer.start_as_current_span(f"{self.module_name}.console.{self.name}")
            if self.tracer is not None
            else nullcontext(None)
        )
        route_path = _normalise_route_path(self.route)
        methods = ",".join(_normalise_route_methods(self.route))
        with span_context as span:
            if span is not None:
                span.set_attribute("coman.module", self.module_name)
                span.set_attribute("coman.operation", self.name)
                if route_path:
                    span.set_attribute("coman.route", route_path)
                if methods:
                    span.set_attribute("coman.methods", methods)
            result = self.endpoint(**bound)
            if inspect.iscoroutine(result):  # pragma: no cover - async endpoints
                return asyncio.run(result)
            return result


class BaseModule:
    name: str = "base"
    version: str | None = None
    description: str = "Base module"
    api_major_version: int = API_MAJOR_VERSION
    enable_legacy_routes: bool = True
    legacy_sunset: date | None = LEGACY_ROUTE_REMOVAL_DATE

    def __init__(self, core: "Core"):
        self.core = core
        self.version = self.version or get_module_version(self.name)
        self.router = APIRouter(
            prefix=f"/v{self.api_major_version}/{self.name}",
            tags=[self.name],
        )
        self._legacy_router: APIRouter | None = None
        legacy_openapi_extra: Dict[str, Any] | None = None
        if self.legacy_sunset is not None:
            legacy_openapi_extra = {"sunset": self.legacy_sunset.isoformat()}
        if self.enable_legacy_routes:
            self._legacy_router = APIRouter(
                prefix=f"/{self.name}",
                tags=[self.name],
                deprecated=True,
            )
            if legacy_openapi_extra is not None:
                self._legacy_router.openapi_extra = dict(legacy_openapi_extra)
        self._legacy_openapi_extra = legacy_openapi_extra
        self._wrap_router_with_legacy_mirroring()
        self._tracer = setup_module_observability(
            self.name,
            self.version,
            router=self.router,
        )
        if self._legacy_router is not None:
            setup_module_observability(
                self.name,
                self.version,
                router=self._legacy_router,
            )

    def get_router(self):
        return self.router

    @property
    def legacy_router(self) -> APIRouter | None:
        return self._legacy_router

    def _wrap_router_with_legacy_mirroring(self) -> None:
        original_add_api_route = self.router.add_api_route

        def add_api_route(
            path: str,
            endpoint: Callable[..., Any],
            *,
            summary: str | None = None,
            deprecated: bool | None = None,
            openapi_extra: Dict[str, Any] | None = None,
            include_in_schema: bool = True,
            methods: Iterable[str] | None = None,
            **kwargs: Any,
        ):
            extra_kwargs = dict(kwargs)
            if "methods" in extra_kwargs and methods is None:
                methods = extra_kwargs.pop("methods")
            else:
                extra_kwargs.pop("methods", None)
            route = original_add_api_route(
                path,
                endpoint,
                summary=summary,
                deprecated=deprecated,
                openapi_extra=openapi_extra,
                include_in_schema=include_in_schema,
                methods=methods,
                **extra_kwargs,
            )
            self._mirror_route_to_legacy(
                path=path,
                endpoint=endpoint,
                summary=summary,
                deprecated=deprecated,
                openapi_extra=openapi_extra,
                include_in_schema=include_in_schema,
                methods=methods,
                route=route,
                extra_kwargs=extra_kwargs,
            )
            return route

        self.router.add_api_route = add_api_route  # type: ignore[assignment]

    def _mirror_route_to_legacy(
        self,
        *,
        path: str,
        endpoint: Callable[..., Any],
        summary: str | None,
        deprecated: bool | None,
        openapi_extra: Dict[str, Any] | None,
        include_in_schema: bool,
        methods: Iterable[str] | None,
        route: Any,
        extra_kwargs: Dict[str, Any],
    ) -> None:
        if not self.enable_legacy_routes or self._legacy_router is None:
            return
        legacy_methods = list(methods or [])
        if not legacy_methods:
            legacy_methods = sorted(route.methods or [])
        if not legacy_methods:
            legacy_methods = ["GET"]
        legacy_kwargs: Dict[str, Any] = dict(extra_kwargs)
        legacy_kwargs.pop("methods", None)
        legacy_kwargs["include_in_schema"] = include_in_schema
        legacy_kwargs["deprecated"] = True
        if summary:
            legacy_kwargs["summary"] = f"[Deprecated] {summary}"
        if openapi_extra or self._legacy_openapi_extra:
            merged_extra: Dict[str, Any] = {}
            if openapi_extra:
                merged_extra.update(openapi_extra)
            if self._legacy_openapi_extra:
                merged_extra.setdefault(
                    "sunset",
                    self._legacy_openapi_extra.get("sunset"),
                )
            legacy_kwargs["openapi_extra"] = merged_extra
        elif self._legacy_openapi_extra:
            legacy_kwargs["openapi_extra"] = dict(self._legacy_openapi_extra)
        if deprecated:
            # Preserve explicit deprecation metadata on the new route.
            legacy_kwargs["deprecated"] = deprecated
        self._legacy_router.add_api_route(
            path,
            endpoint,
            methods=legacy_methods,
            **legacy_kwargs,
        )

    def get_routers(self) -> List[APIRouter]:
        routers = [self.router]
        if self._legacy_router is not None:
            routers.append(self._legacy_router)
        return routers

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
            op = ConsoleOperation(
                name=base_name,
                route=route,
                endpoint=endpoint,
                module_name=self.name,
                tracer=getattr(self, "_tracer", None),
            )
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
                module_name=self.name,
                tracer=getattr(self, "_tracer", None),
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
