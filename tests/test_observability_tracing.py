from __future__ import annotations

from importlib import metadata

from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from core.base_module import BaseModule
from observability import tracing


class _DummyCore:
    pass


class DummyModule(BaseModule):
    name = "dummy"
    version = "1.2.3"

    def __init__(self) -> None:
        super().__init__(_DummyCore())

        @self.router.get("/ping")
        async def ping() -> dict[str, str]:
            return {"status": "ok"}


def test_module_routes_emit_custom_spans() -> None:
    module = DummyModule()
    provider = tracing._PROVIDERS[module.name]  # type: ignore[attr-defined]
    exporter = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(exporter))

    result = module.invoke_console_operation("ping")
    assert result == {"status": "ok"}

    spans = exporter.get_finished_spans()
    assert spans, "expected at least one span"
    span = spans[-1]
    assert span.resource.attributes.get("service.name") == module.name
    assert span.resource.attributes.get("service.version") == metadata.version("coman")
    assert span.attributes["coman.module"] == module.name
    assert span.attributes["coman.operation"].endswith("ping")
    assert span.attributes["coman.route"].endswith("/ping")

    exporter.clear()
