from __future__ import annotations
from fastapi import APIRouter
class BaseModule:
    name: str = "base"
    version: str = "0.4.0"
    description: str = "Base module"
    def __init__(self, core: "Core"):
        self.core = core
        self.router = APIRouter(prefix=f"/{self.name}", tags=[self.name])
    def get_router(self): return self.router
    def register_schedules(self): pass
