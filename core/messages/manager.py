from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

try:  # pragma: no cover - optional import (pydantic v1 compatibility)
    from pydantic import Field
except ImportError:  # pragma: no cover
    from pydantic import Field  # type: ignore

from .base import ModuleMessage, ModuleRequest, ModuleResponse


class ToolDefinition(ModuleMessage):
    """Definition of a callable tool exposed by a module."""

    name: str
    method: str = "GET"
    path: str
    params: List[str] = Field(default_factory=list)
    desc: str = ""

    def __init__(self, **data: Any) -> None:  # pragma: no cover - exercised via endpoints
        params = data.get("params")
        if isinstance(params, str):
            data["params"] = [p.strip() for p in params.split(",") if p.strip()]
        super().__init__(**data)
        self.method = (self.method or "GET").upper()
        self.params = [p for p in (self.params or []) if p]


class ToolRegistry(ModuleResponse):
    """Collection of tools registered in the system."""

    tools: List[ToolDefinition] = Field(default_factory=list)

    def upsert(self, tool: ToolDefinition) -> None:
        existing = [t for t in self.tools if t.name != tool.name]
        existing.append(tool)
        self.tools = existing

    def find(self, name: str) -> Optional[ToolDefinition]:
        for tool in self.tools:
            if tool.name == name:
                return tool
        return None

    def names(self) -> List[str]:
        return [t.name for t in self.tools]

    @classmethod
    def from_tools(cls, tools: Iterable[ToolDefinition]) -> "ToolRegistry":
        return cls(tools=list(tools))


class ManagerRunRequest(ModuleRequest):
    """Request payload for the manager's /run endpoint."""

    goal: str = ""
    inputs: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def __init__(self, **data: Any) -> None:  # pragma: no cover - via FastAPI
        inputs = data.get("inputs") or {}
        metadata = data.get("metadata") or {}
        if not isinstance(inputs, dict):
            inputs = {}
        if not isinstance(metadata, dict):
            metadata = {}
        data.update({"inputs": inputs, "metadata": metadata})
        super().__init__(**data)
        self.goal = (self.goal or "").strip()


class ManagerRunResult(ModuleResponse):
    """Structured response returned by the manager."""

    goal: str = ""
    tool: Optional[str] = None
    query: Dict[str, Any] = Field(default_factory=dict)
    result: Any | None = None
    error: Optional[str] = None
    message: Optional[str] = None
    known_tools: Optional[ToolRegistry] = None

    def set_known_tools(self, registry: ToolRegistry) -> "ManagerRunResult":
        self.known_tools = registry
        return self
