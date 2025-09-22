from __future__ import annotations
from coman.core.base_module import BaseModule
from fastapi import Query
class Module(BaseModule):
    name = "text"; description = "Simple text utilities"
    def __init__(self, core):
        super().__init__(core)
        @self.router.get("/uppercase")
        def uppercase(s: str = Query(..., min_length=1)):
            return {"result": s.upper()}
