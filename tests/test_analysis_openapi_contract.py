from __future__ import annotations

from collections.abc import Mapping

import jsonschema
import pytest
from fastapi.testclient import TestClient

from modules.analysis_module.app.main import app as analysis_app


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


def test_analysis_openapi_contract_validates_request_and_response() -> None:
    client = TestClient(analysis_app)
    document = client.get("/openapi.json").json()
    path_item = document["paths"]["/v1/analysis/frequency"]["post"]

    request_schema = _resolve_ref(
        path_item["requestBody"]["content"]["application/json"]["schema"],
        document,
    )
    response_schema = _resolve_ref(
        path_item["responses"]["200"]["content"]["application/json"]["schema"],
        document,
    )
    error_schema = _resolve_ref(
        path_item["responses"]["422"]["content"]["application/json"]["schema"],
        document,
    )

    request_validator = _validator(request_schema, document)
    response_validator = _validator(response_schema, document)
    error_validator = _validator(error_schema, document)

    request_validator.validate({"text": "Hello world"})
    response = client.post("/v1/analysis/frequency", json={"text": "Hello world"})
    assert response.status_code == 200
    response_validator.validate(response.json())

    error_response = client.post("/v1/analysis/frequency", json={"text": "   "})
    assert error_response.status_code == 422
    error_validator.validate(error_response.json())


