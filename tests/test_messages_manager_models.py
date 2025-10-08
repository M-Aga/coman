from __future__ import annotations

from core.messages.manager import (
    ManagerRunRequest,
    ManagerRunResult,
    ToolDefinition,
    ToolRegistry,
)


def test_tool_definition_normalises_payload() -> None:
    payload = {
        "name": "example",
        "method": "post",
        "path": "/v1/example",
        "params": "a, b ,",
    }
    tool = ToolDefinition.from_payload(payload)
    assert tool.method == "POST"
    assert tool.params == ["a", "b"]


def test_tool_registry_roundtrip_and_lookup() -> None:
    tools = [
        ToolDefinition(name="first", path="/a"),
        ToolDefinition(name="second", path="/b"),
    ]
    registry = ToolRegistry.from_tools(tools)
    registry.upsert(ToolDefinition(name="first", path="/other"))

    assert registry.names() == ["second", "first"]
    found = registry.find("first")
    assert found is not None
    assert found.path == "/other"


def test_manager_run_request_sanitises_inputs() -> None:
    payload = {
        "goal": "  explore  ",
        "inputs": ["not", "a", "dict"],
        "metadata": None,
    }
    request = ManagerRunRequest.from_payload(payload)
    assert request.goal == "explore"
    assert request.inputs == {}
    assert request.metadata == {}


def test_manager_run_result_sets_known_tools() -> None:
    registry = ToolRegistry()
    result = ManagerRunResult(goal="demo").set_known_tools(registry)
    assert result.known_tools is registry
