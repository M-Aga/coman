"""Tracing utilities for Coman modules and FastAPI applications."""

from __future__ import annotations

import logging
import os
from importlib import metadata
from threading import Lock
from typing import Any, Callable

from fastapi import APIRouter, FastAPI
from fastapi.routing import APIRoute
from starlette.requests import Request
from starlette.responses import Response
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)
from opentelemetry.trace import Tracer
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

from core.config import settings

_LOG = logging.getLogger(__name__)

_PROVIDER_LOCK = Lock()
_PROVIDERS: dict[str, TracerProvider] = {}
_HTTPX_INSTRUMENTED = False
_REQUESTS_INSTRUMENTED = False


def _default_version() -> str:
    try:
        return metadata.version("coman")
    except metadata.PackageNotFoundError:
        return "0.0.0"


def _normalise_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    lowered = value.strip().lower()
    if lowered in {"0", "false", "no", "off"}:
        return False
    if lowered in {"1", "true", "yes", "on"}:
        return True
    return default


def _build_resource(service_name: str, service_version: str | None) -> Resource:
    attributes = {
        "service.name": service_name,
        "service.namespace": "coman",
        "service.version": service_version or _default_version(),
    }
    return Resource.create(attributes)


def _configure_exporters(provider: TracerProvider, service_name: str) -> None:
    enable_otlp = _normalise_bool(os.getenv("COMAN_OTEL_OTLP_ENABLED"), True)
    if enable_otlp:
        endpoint = (
            os.getenv("COMAN_OTEL_EXPORTER_OTLP_ENDPOINT")
            or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
            or "http://localhost:4318/v1/traces"
        )
        headers = os.getenv("COMAN_OTEL_EXPORTER_OTLP_HEADERS") or os.getenv(
            "OTEL_EXPORTER_OTLP_HEADERS", ""
        )
        timeout = float(os.getenv("COMAN_OTEL_EXPORTER_OTLP_TIMEOUT", "10"))
        exporter = OTLPSpanExporter(endpoint=endpoint, headers=headers, timeout=timeout)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        _LOG.debug(
            "Configured OTLP exporter for service %s -> %s", service_name, endpoint
        )

    if settings.env == "dev":
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
        _LOG.debug("Enabled console span exporter for service %s in dev mode", service_name)


def _get_or_create_provider(service_name: str, service_version: str | None) -> TracerProvider:
    with _PROVIDER_LOCK:
        provider = _PROVIDERS.get(service_name)
        if provider is None:
            resource = _build_resource(service_name, service_version)
            provider = TracerProvider(resource=resource)
            _configure_exporters(provider, service_name)
            _PROVIDERS[service_name] = provider
            _LOG.debug(
                "Created tracer provider for service %s with resource %s",
                service_name,
                resource.attributes,
            )
        return provider


def _ensure_global_provider(provider: TracerProvider, service_name: str) -> None:
    current = trace.get_tracer_provider()
    current_name = getattr(current, "_coman_service_name", None)
    if current_name == service_name:
        return
    if isinstance(current, TracerProvider) and current_name:
        return
    if isinstance(current, TracerProvider) and not current_name:
        # Respect an externally configured provider.
        return
    if type(current).__name__ == "DefaultTracerProvider":
        trace.set_tracer_provider(provider)
        setattr(provider, "_coman_service_name", service_name)
        _LOG.debug("Registered %s as global tracer provider", service_name)


def _instrument_http_clients(provider: TracerProvider) -> None:
    global _HTTPX_INSTRUMENTED, _REQUESTS_INSTRUMENTED
    if not _HTTPX_INSTRUMENTED:
        HTTPXClientInstrumentor().instrument(tracer_provider=provider)
        _HTTPX_INSTRUMENTED = True
        _LOG.debug("Instrumented httpx client with provider %s", provider)
    if not _REQUESTS_INSTRUMENTED:
        RequestsInstrumentor().instrument(tracer_provider=provider)
        _REQUESTS_INSTRUMENTED = True
        _LOG.debug("Instrumented requests client with provider %s", provider)


def _build_route_class(module_name: str, tracer: Tracer) -> type[APIRoute]:
    class TracedAPIRoute(APIRoute):
        def get_route_handler(self) -> Callable[[Request], Any]:
            original_handler = super().get_route_handler()
            operation = self.name or getattr(self.endpoint, "__name__", "")
            route_path = self.path
            methods = sorted(self.methods or [])

            async def traced_handler(request: Request) -> Response:
                span_name = f"{module_name}.{operation.strip('/') or route_path.strip('/') or 'handler'}"
                with tracer.start_as_current_span(span_name) as span:
                    span.set_attribute("coman.module", module_name)
                    span.set_attribute("coman.operation", operation or route_path)
                    span.set_attribute("coman.route", route_path)
                    if methods:
                        span.set_attribute("coman.methods", ",".join(methods))
                    return await original_handler(request)

            return traced_handler

    return TracedAPIRoute


def _ensure_router_route_class(router: APIRouter, tracer: Tracer, module_name: str) -> None:
    if getattr(router, "_coman_tracing_route_class", None):  # pragma: no cover - defensive
        return
    router.route_class = _build_route_class(module_name, tracer)
    setattr(router, "_coman_tracing_route_class", router.route_class)


def setup_module_observability(
    module_name: str,
    module_version: str | None = None,
    *,
    router: APIRouter | None = None,
) -> Tracer:
    """Configure tracing for a module router and return the tracer."""

    provider = _get_or_create_provider(module_name, module_version)
    tracer = provider.get_tracer(f"coman.modules.{module_name}")
    if router is not None:
        _ensure_router_route_class(router, tracer, module_name)
    return tracer


def instrument_fastapi_app(
    app: FastAPI,
    module_name: str,
    module_version: str | None = None,
) -> Tracer:
    """Auto-instrument a FastAPI app and HTTP clients for a module."""

    provider = _get_or_create_provider(module_name, module_version)
    tracer = provider.get_tracer(f"coman.modules.{module_name}")
    FastAPIInstrumentor().instrument_app(app, tracer_provider=provider)
    _instrument_http_clients(provider)
    _ensure_global_provider(provider, module_name)
    return tracer

