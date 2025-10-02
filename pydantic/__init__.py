"""Compatibility wrapper that exposes the real Pydantic package when installed."""

from __future__ import annotations

import importlib
import importlib.machinery
import importlib.util
import os
import site
import sys
import sysconfig
from pathlib import Path
from types import ModuleType
from typing import Iterable


def _iter_site_packages() -> Iterable[str]:
    seen: set[str] = set()

    for getter_name in ("getsitepackages", "getusersitepackages"):
        getter = getattr(site, getter_name, None)
        if getter is None:
            continue
        try:
            value = getter()
        except Exception:  # pragma: no cover - defensive guard
            continue
        if isinstance(value, str):
            candidates = [value]
        else:
            candidates = list(value)
        for path in candidates:
            if path and path not in seen:
                seen.add(path)
                yield path

    for key in ("purelib", "platlib"):
        try:
            path = sysconfig.get_path(key)
        except KeyError:  # pragma: no cover - defensive
            continue
        if path and path not in seen:
            seen.add(path)
            yield path


def _load_real_pydantic() -> ModuleType | None:
    finder = importlib.machinery.PathFinder

    for root in _iter_site_packages():
        spec = finder.find_spec("pydantic", [root])
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules[__name__] = module
            spec.loader.exec_module(module)
            return module

    placeholder = sys.modules.pop(__name__, None)
    try:
        module = importlib.import_module("pydantic")
    except Exception:
        module = None
    finally:
        if placeholder is not None:
            sys.modules[__name__] = placeholder

    if module is not None:
        module_path = getattr(module, "__file__", None)
        if module_path and Path(module_path).resolve() != Path(__file__).resolve():
            return module

    return None


_real_pydantic: ModuleType | None = None

if os.environ.get("COMAN_USE_PYDANTIC_STUB") != "1":
    _real_pydantic = _load_real_pydantic()

if _real_pydantic is not None:
    globals().update(_real_pydantic.__dict__)
    sys.modules[__name__] = _real_pydantic
else:
    from typing import Any, Dict, Mapping, MutableMapping

    __all__ = [
        "BaseModel",
        "ConfigDict",
        "Field",
        "ValidationError",
    ]

    _missing = object()

    class ValidationError(Exception):
        """Simplified validation error used by the test suite."""

    class ConfigDict(dict):
        """Placeholder mapping to satisfy code paths expecting pydantic v2."""

    class FieldInfo:
        def __init__(self, default: Any = _missing, default_factory: Any = None):
            self.default = default
            self.default_factory = default_factory

    def Field(*, default: Any = _missing, default_factory: Any | None = None) -> FieldInfo:
        if default is not _missing and default_factory is not None:
            raise ValueError("Specify either default or default_factory")
        return FieldInfo(default=default, default_factory=default_factory)

    class BaseModel:
        """Very small subset of Pydantic's BaseModel behaviour."""

        model_config = ConfigDict()
        model_fields: Dict[str, Any] = {}

        def __init_subclass__(cls, **kwargs: Any) -> None:
            super().__init_subclass__(**kwargs)
            annotations = getattr(cls, "__annotations__", {})
            cls.model_fields = {name: None for name in annotations}
            cls.__fields__ = cls.model_fields

        def __init__(self, **data: Any) -> None:
            cls = self.__class__
            annotations = getattr(cls, "__annotations__", {})
            remaining = dict(data)
            for name in annotations:
                if name in remaining:
                    value = remaining.pop(name)
                else:
                    value = self._default_for(name)
                setattr(self, name, value)
            for key, value in remaining.items():
                setattr(self, key, value)

        @classmethod
        def _field_info(cls, name: str) -> FieldInfo | Any:
            return getattr(cls, name, _missing)

        @classmethod
        def _default_for(cls, name: str) -> Any:
            info = cls._field_info(name)
            if isinstance(info, FieldInfo):
                if info.default_factory is not None:
                    return info.default_factory()
                if info.default is not _missing:
                    return info.default
                return None
            if info is not _missing:
                return info
            return None

        @classmethod
        def parse_obj(cls, obj: Mapping[str, Any] | MutableMapping[str, Any]) -> "BaseModel":
            if not isinstance(obj, Mapping):
                raise ValidationError("Expected mapping for parse_obj")
            return cls(**dict(obj))

        @classmethod
        def model_validate(cls, obj: Mapping[str, Any]) -> "BaseModel":
            if not isinstance(obj, Mapping):
                raise ValidationError("Expected mapping for model_validate")
            return cls(**dict(obj))

        def dict(self, *, exclude_none: bool = False) -> Dict[str, Any]:
            return self._to_dict(exclude_none=exclude_none)

        def model_dump(self, *, exclude_none: bool = False) -> Dict[str, Any]:
            return self._to_dict(exclude_none=exclude_none)

        def _to_dict(self, *, exclude_none: bool) -> Dict[str, Any]:
            result: Dict[str, Any] = {}
            for name in getattr(self.__class__, "__annotations__", {}):
                value = getattr(self, name, None)
                if exclude_none and value is None:
                    continue
                result[name] = self._normalise(value, exclude_none=exclude_none)
            return result

        @classmethod
        def _normalise(cls, value: Any, *, exclude_none: bool) -> Any:
            if isinstance(value, BaseModel):
                return value._to_dict(exclude_none=exclude_none)
            if isinstance(value, list):
                return [cls._normalise(item, exclude_none=exclude_none) for item in value]
            if isinstance(value, tuple):
                return tuple(cls._normalise(item, exclude_none=exclude_none) for item in value)
            if isinstance(value, dict):
                return {key: cls._normalise(val, exclude_none=exclude_none) for key, val in value.items()}
            return value

        def __repr__(self) -> str:  # pragma: no cover - debug helper
            fields = ", ".join(f"{name}={getattr(self, name, None)!r}" for name in self.model_fields)
            return f"{self.__class__.__name__}({fields})"
