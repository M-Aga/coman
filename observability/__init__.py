"""Observability helpers for Coman."""

from .tracing import (
    instrument_fastapi_app,
    setup_module_observability,
)

__all__ = [
    "instrument_fastapi_app",
    "setup_module_observability",
]

