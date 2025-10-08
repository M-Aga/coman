from contextlib import asynccontextmanager

from fastapi import FastAPI

from observability import instrument_fastapi_app
from coman.version import (
    API_MAJOR_VERSION,
    COMAN_VERSION,
    LEGACY_ROUTE_REMOVAL_DATE,
)

from .registry import Core
from .scheduler import Scheduler
from coman.modules.ui.mount import mount_ui


def build_fastapi_app(core: Core) -> FastAPI:
    core.scheduler = Scheduler()

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        core.scheduler.start()
        try:
            yield
        finally:
            core.scheduler.shutdown()

    app = FastAPI(title="Coman API", version=COMAN_VERSION, lifespan=lifespan)
    instrument_fastapi_app(app, module_name="core", module_version=COMAN_VERSION)

    legacy_metadata = {"sunset": LEGACY_ROUTE_REMOVAL_DATE.isoformat()}

    @app.get(f"/v{API_MAJOR_VERSION}/health")
    def health() -> dict[str, object]:
        return {"status": "ok", "modules": list(core.modules.keys())}

    @app.get("/health", deprecated=True, openapi_extra=legacy_metadata)
    def legacy_health() -> dict[str, object]:
        return health()

    for m in core.modules.values():
        routers = getattr(m, "get_routers", None)
        if callable(routers):
            for router in routers():
                app.include_router(router)
        else:  # pragma: no cover - compatibility fallback
            app.include_router(m.get_router())
        try:
            m.register_schedules()
        except Exception:
            pass

    mount_ui(app)
    return app
