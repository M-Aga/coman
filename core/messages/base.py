from __future__ import annotations

from typing import Any, Dict, Type, TypeVar

try:  # pragma: no cover - compatibility shim
    from pydantic import BaseModel, ConfigDict, ValidationError
except ImportError:  # pragma: no cover
    from pydantic import BaseModel, ValidationError  # type: ignore
    ConfigDict = None  # type: ignore

T = TypeVar("T", bound="ModuleMessage")


class ModuleMessage(BaseModel):
    """Base class for serialisable messages exchanged between modules."""

    if "ConfigDict" in globals() and ConfigDict is not None:  # Pydantic v2
        model_config = ConfigDict(populate_by_name=True, extra="ignore")  # type: ignore[attr-defined]
    else:  # pragma: no cover - Pydantic v1 fallback
        class Config:
            allow_population_by_field_name = True
            extra = "ignore"

    @classmethod
    def from_payload(cls: Type[T], payload: Any | None = None) -> T:
        """Create an instance from arbitrary payload data."""

        if isinstance(payload, cls):
            return payload
        if payload is None:
            payload = {}
        try:
            if hasattr(cls, "model_validate"):  # Pydantic v2
                return cls.model_validate(payload)  # type: ignore[attr-defined]
            return cls.parse_obj(payload)  # type: ignore[call-arg]
        except ValidationError:
            # fall back to constructing with the subset of recognised keys
            data: Dict[str, Any] = {}
            for field in getattr(cls, "model_fields", getattr(cls, "__fields__", {})):
                if isinstance(payload, dict) and field in payload:
                    data[field] = payload[field]
            if hasattr(cls, "model_validate"):
                return cls.model_validate(data)  # type: ignore[attr-defined]
            return cls.parse_obj(data)  # type: ignore[call-arg]

    def to_payload(self) -> Dict[str, Any]:
        """Return a plain JSON-serialisable payload."""

        if hasattr(self, "model_dump"):
            return self.model_dump(exclude_none=True)  # type: ignore[attr-defined]
        return self.dict(exclude_none=True)  # type: ignore[call-arg]

    def clone(self: T, **updates: Any) -> T:
        data = self.to_payload()
        data.update(updates)
        return self.__class__.from_payload(data)


class ModuleRequest(ModuleMessage):
    """Marker base class for request payloads."""


class ModuleResponse(ModuleMessage):
    """Marker base class for response payloads."""
