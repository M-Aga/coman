from __future__ import annotations
from coman.core.base_module import BaseModule
import psutil
class Module(BaseModule):
    name = "resources"; description = "CPU/Mem snapshot"
    def __init__(self, core):
        super().__init__(core)
        @self.router.get("/snapshot")
        def snapshot():
            return {"cpu_percent": psutil.cpu_percent(interval=0.3),
                    "mem": dict(psutil.virtual_memory()._asdict())}
