from fastapi import FastAPI
from .registry import Core
from .scheduler import Scheduler
from coman.modules.ui.mount import mount_ui
def build_fastapi_app(core: Core) -> FastAPI:
    app = FastAPI(title="Coman API", version="0.4.0")
    core.scheduler = Scheduler(); core.scheduler.start()
    @app.get("/health")
    def health(): return {"status": "ok", "modules": list(core.modules.keys())}
    for m in core.modules.values():
        app.include_router(m.get_router())
        try: m.register_schedules()
        except Exception: pass
    mount_ui(app)
    return app
