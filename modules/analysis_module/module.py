from __future__ import annotations
from coman.core.base_module import BaseModule
class Module(BaseModule):
    name = "analysis"; description = "Light text analysis"
    def __init__(self, core):
        super().__init__(core)
        @self.router.post("/frequency")
        def frequency(text: str):
            from collections import Counter
            words = [w.lower() for w in text.split() if w.strip()]
            return dict(Counter(words))
