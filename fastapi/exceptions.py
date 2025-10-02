class HTTPException(Exception):
    """Minimal HTTPException compatible with FastAPI's behaviour."""

    def __init__(self, status_code: int, detail: str | None = None):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail
