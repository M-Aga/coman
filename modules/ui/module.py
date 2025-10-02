from __future__ import annotations
from coman.core.base_module import BaseModule
class Module(BaseModule):
    name = "ui"; description = "UI stub; endpoints mounted in app via mount_ui()"
    def __init__(self, core):
        super().__init__(core)
