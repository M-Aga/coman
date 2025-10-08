from __future__ import annotations

from typing import Any

import pytest

from fastapi import Query

from core.base_module import (
    BaseModule,
    ConsoleOperation,
    _coerce_parameter_value,
    _is_fastapi_param,
    _normalise_route_methods,
    _normalise_route_path,
)


class DummyRoute:
    def __init__(self, methods: set[str] | None = None, path: str = "/demo", summary: str = "demo") -> None:
        self.methods = methods
        self.path = path
        self.summary = summary
        self.endpoint = lambda value=1: value
        self.method = None
        self.path_format = None


def test_normalise_route_methods_and_path() -> None:
    route = DummyRoute(methods={"get", "POST"}, path="/items/{item_id}")
    assert _normalise_route_methods(route) == ["GET", "POST"]
    assert _normalise_route_path(route) == "/items/{item_id}"


def test_normalise_route_methods_with_single_method_attribute() -> None:
    route = DummyRoute(methods=None)
    route.method = "patch"
    assert _normalise_route_methods(route) == ["PATCH"]


def test_normalise_route_path_uses_path_format_fallback() -> None:
    route = DummyRoute(path="")
    route.path_format = "/formatted"
    assert _normalise_route_path(route) == "/formatted"


@pytest.mark.parametrize(
    ("raw", "annotation", "expected"),
    [
        ("[1, 2]", list[int], [1, 2]),
        ("{\"k\": 1}", dict[str, int], {"k": 1}),
        ("not-json", list[str], ["not-json"]),
    ],
)
def test_coerce_parameter_value_handles_json(raw: str, annotation: Any, expected: Any) -> None:
    assert _coerce_parameter_value(raw, annotation) == expected


def test_is_fastapi_param_detects_wrappers() -> None:
    assert _is_fastapi_param(Query(default="value"))
    assert not _is_fastapi_param(object())


def test_console_operation_invokes_endpoint() -> None:
    class DummyCore:
        pass

    module = BaseModule(DummyCore())

    @module.router.get("/sample", summary="Sample")
    def endpoint(value: int = 1) -> int:
        return value

    operations = module.get_console_operations()
    op = operations["sample"]
    assert isinstance(op, ConsoleOperation)
    assert op.describe()["path"] == "/base/sample"
    assert op.invoke({"value": 3}) == 3
    assert module.describe_console_operations()[0]["methods"] == ["GET"]

    with pytest.raises(KeyError):
        module.invoke_console_operation("unknown")
