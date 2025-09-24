from __future__ import annotations

from typing import List

try:  # pragma: no cover - optional import for pydantic v1
    from pydantic import Field
except ImportError:  # pragma: no cover
    from pydantic import Field  # type: ignore

from .base import ModuleResponse


class Capability(ModuleResponse):
    """Description of a capability exposed by a module."""

    name: str
    kind: str = "webhook"
    endpoint: str = ""
    description: str = ""

    def __init__(self, **data):  # pragma: no cover
        super().__init__(**data)
        self.kind = (self.kind or "webhook").strip() or "webhook"
        self.endpoint = self.endpoint.strip()
        self.description = self.description.strip()


class CapabilityRegistry(ModuleResponse):
    """Registry of capabilities."""

    capabilities: List[Capability] = Field(default_factory=list)

    def add(self, capability: Capability) -> None:
        self.capabilities.append(capability)
