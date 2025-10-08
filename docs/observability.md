# Observability

## Design options

1. **Module-aware tracer providers (chosen).** Each module initialises a dedicated
   OpenTelemetry tracer provider with a `service.name` that matches the module and
   wraps its routers to emit custom spans at the module boundary. Pros: spans are
   tagged with module-specific resources, cross-module calls remain correlated, and
   HTTP client instrumentation inherits the active module context. Cons: requires
   lightweight wrapper logic on every router and a small coordination layer to
   reuse providers across apps.
2. **Single global tracer provider.** Configure one provider for the entire
   process and rely solely on the FastAPI/ASGI auto-instrumentor. Pros: minimal
   implementation effort. Cons: all spans share the same service identity, making
   it difficult to distinguish module ownership and to reason about nested spans.

**Chosen approach:** Option 1 keeps module ownership visible in traces without
introducing complex plumbing. The additional wrapper ensures every module
boundary yields a custom span while still leveraging FastAPI and HTTP client
auto-instrumentation.

## Running the collector stack locally

1. Start the OpenTelemetry Collector and Jaeger backend:

   ```bash
   docker compose up --build
   ```

2. Point Coman to the collector (the default matches the compose file, so this is
   optional):

   ```bash
   export COMAN_OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4318/v1/traces"
   ```

3. Launch the application (for example, the aggregated FastAPI API):

   ```bash
   uv run python -m modules.main api
   ```

4. Exercise a module endpoint (e.g. `http://127.0.0.1:8000/v1/text/uppercase`) to
   generate traces.

> **Tip:** When running unit tests or working without the collector, export
> `COMAN_OTEL_OTLP_ENABLED=0` to silence the OTLP exporter while keeping the
> console spans enabled in development.

## Viewing traces

1. Open Jaeger at <http://localhost:16686>.
2. Select the desired `service.name` (e.g. `core`, `analysis`, or `text`).
3. Run a query to inspect traces; spans emitted from module wrappers include
   attributes such as `coman.module`, `coman.operation`, and `coman.route` to
   make ownership explicit.
4. During development (`COMAN_ENV=dev`) spans are also mirrored to stdout via the
   console exporter for quick feedback.
