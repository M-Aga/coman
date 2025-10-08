from __future__ import annotations

from pydantic import Field

from core.messages.base import ModuleMessage


class SampleMessage(ModuleMessage):
    identifier: int = 0
    alias_value: str = Field(default="", alias="aliasValue")


def test_module_message_from_payload_handles_aliases_and_unknown_fields() -> None:
    payload = {"identifier": "7", "aliasValue": "value", "ignored": "data"}
    message = SampleMessage.from_payload(payload)
    assert message.identifier == 7
    assert message.alias_value == "value"
    assert message.to_payload() == {"identifier": 7, "alias_value": "value"}


def test_module_message_clone_updates_fields() -> None:
    original = SampleMessage(identifier=1, alias_value="alpha")
    cloned = original.clone(identifier=2)
    assert cloned.identifier == 2
    assert cloned.alias_value == "alpha"
    assert original.identifier == 1
