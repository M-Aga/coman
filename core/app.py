from contextlib import asynccontextmanager

from fastapi import FastAPI

from observability import instrument_fastapi_app

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

    app = FastAPI(title="Coman API", version="0.4.0", lifespan=lifespan)
    instrument_fastapi_app(app, module_name="core", module_version="0.4.0")

    @app.get("/health")
    def health():
        return {"status": "ok", "modules": list(core.modules.keys())}

    for m in core.modules.values():
        app.include_router(m.get_router())
        try:
            m.register_schedules()
        except Exception:
            pass

    mount_ui(app)
    return app
