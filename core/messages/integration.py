from __future__ import annotations

from typing import Any, Dict, List, Optional

try:  # pragma: no cover - optional import (pydantic v1 compatibility)
    from pydantic import Field
except ImportError:  # pragma: no cover
    from pydantic import Field  # type: ignore

from .base import ModuleRequest, ModuleResponse


class IntegrationDefinition(ModuleResponse):
    """Definition of an integration adapter."""

    name: str
    path: str
    module: str
    callable: str
    sig: Optional[str] = None

    def __init__(self, **data: Any) -> None:  # pragma: no cover - invoked by FastAPI
        super().__init__(**data)
        self.name = self.name.strip()
        self.path = self.path.strip()
        self.module = self.module.strip()
        self.callable = self.callable.strip()
        if self.sig:
            self.sig = self.sig.strip()


class IntegrationRegistry(ModuleResponse):
    """Collection of registered integrations."""

    integrations: List[IntegrationDefinition] = Field(default_factory=list)

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self._ensure_models()

    def upsert(self, integration: IntegrationDefinition) -> None:
        self._ensure_models()
        current = [it for it in self.integrations if it.name != integration.name]
        current.append(integration)
        self.integrations = current

    def find(self, name: str) -> Optional[IntegrationDefinition]:
        self._ensure_models()
        for it in self.integrations:
            if it.name == name:
                return it
        return None

    def _ensure_models(self) -> None:
        converted: List[IntegrationDefinition] = []
        for item in self.integrations:
            if isinstance(item, IntegrationDefinition):
                converted.append(item)
            else:
                converted.append(IntegrationDefinition.from_payload(item))
        self.integrations = converted


class IntegrationCallRequest(ModuleRequest):
    """Request payload for executing an integration."""

    name: str
    callable: Optional[str] = None
    kwargs: Dict[str, Any] = Field(default_factory=dict)
    mode: str = "inproc"
    verify_sig: bool = True

    def __init__(self, **data: Any) -> None:  # pragma: no cover
        kwargs = data.get("kwargs") or {}
        if not isinstance(kwargs, dict):
            kwargs = {}
        if "kwargs" in kwargs and len(kwargs) == 1 and isinstance(kwargs["kwargs"], dict):
            kwargs = kwargs["kwargs"]
        data.update({"kwargs": kwargs})
        super().__init__(**data)
        self.mode = (self.mode or "inproc").strip() or "inproc"


class IntegrationCallResult(ModuleResponse):
    """Response returned by the integration module."""

    result: Any | None = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    ok: Optional[bool] = None
