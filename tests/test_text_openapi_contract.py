from __future__ import annotations

from collections.abc import Mapping

import jsonschema
import pytest
from fastapi.testclient import TestClient

from modules.text_module.app.main import app as text_app


def _resolve_ref(schema: Mapping[str, object], document: Mapping[str, object]) -> Mapping[str, object]:
    if "$ref" not in schema:
        return schema
    ref: str = schema["$ref"]  # type: ignore[assignment]
    assert ref.startswith("#/"), "Only local references are supported in the test suite"
    parts = ref.lstrip("#/").split("/")
    node: object = document
    for part in parts:
        if isinstance(node, Mapping):
            node = node[part]
        else:  # pragma: no cover - defensive
            raise KeyError(ref)
    assert isinstance(node, Mapping)
    return node  # type: ignore[return-value]


def _validator(
    schema: Mapping[str, object],
    document: Mapping[str, object] | None = None,
) -> jsonschema.Draft202012Validator:
    resolver = None
    if document is not None:
        resolver = jsonschema.RefResolver.from_schema(document)  # type: ignore[attr-defined]
    return jsonschema.Draft202012Validator(schema, resolver=resolver)  # type: ignore[arg-type]


def test_text_openapi_contract_validates_request_response_and_legacy() -> None:
    client = TestClient(text_app)
    document = client.get("/openapi.json").json()
    post_path = document["paths"]["/v1/text/uppercase"]["post"]

    request_schema = _resolve_ref(
        post_path["requestBody"]["content"]["application/json"]["schema"],
        document,
    )
    response_schema = _resolve_ref(
        post_path["responses"]["200"]["content"]["application/json"]["schema"],
        document,
    )
    error_schema = _resolve_ref(
        post_path["responses"]["422"]["content"]["application/json"]["schema"],
        document,
    )

    request_validator = _validator(request_schema, document)
    response_validator = _validator(response_schema, document)
    error_validator = _validator(error_schema, document)

    request_validator.validate({"text": "Hello"})
    response = client.post("/v1/text/uppercase", json={"text": "Hello"})
    assert response.status_code == 200
    response_validator.validate(response.json())

    legacy_response = client.get("/text/uppercase", params={"text": "Hello"})
    assert legacy_response.status_code == 200
    response_validator.validate(legacy_response.json())

    error_response = client.post("/v1/text/uppercase", json={"text": "   "})
    assert error_response.status_code == 422
    error_validator.validate(error_response.json())
