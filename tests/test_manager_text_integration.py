from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from core.app import build_fastapi_app
from core.registry import Core
from modules.manager import module as manager_module
from modules.text_module import module as text_module


class _LocalHttpClient:
    def __init__(self, test_client: TestClient, base_url: str) -> None:
        self._client = test_client
        self._base_url = base_url.rstrip("/")

    def __enter__(self) -> "_LocalHttpClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:  # type: ignore[override]
        return False

    def _request(self, method: str, url: str, **kwargs: Any):
        assert url.startswith(self._base_url)
        path = url[len(self._base_url) :]
        if not path:
            path = "/"
        return self._client.request(method, path, **kwargs)

    def get(self, url: str, **kwargs: Any):
        return self._request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any):
        return self._request("POST", url, **kwargs)


def test_manager_invokes_text_module_end_to_end(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(manager_module, "mount_ui", lambda _app: None, raising=False)
    monkeypatch.setattr("core.app.mount_ui", lambda _app: None)

    monkeypatch.setattr(manager_module.settings, "data_dir", str(tmp_path), raising=False)
    monkeypatch.setattr(manager_module.settings, "api_base", "http://testserver", raising=False)

    core = Core()
    manager = manager_module.Module(core)
    text = text_module.Module(core)
    core.modules = {manager.name: manager, text.name: text}

    app = build_fastapi_app(core)
    client = TestClient(app)
    base_url = str(client.base_url).rstrip("/")
    monkeypatch.setattr(manager_module.settings, "api_base", base_url, raising=False)

    def _client_factory(*args: Any, **kwargs: Any) -> _LocalHttpClient:
        return _LocalHttpClient(client, base_url)

    monkeypatch.setattr(manager_module.httpx, "Client", _client_factory)

    registry = manager_module.ToolRegistry()
    registry.upsert(
        manager_module.ToolDefinition(
            name="text.uppercase",
            method="GET",
            path="/text/uppercase",
            params=["s"],
        )
    )
    manager_module.save_tools(registry)

    response = client.post("/manager/run", json={"goal": "uppercase this", "inputs": {}})
    assert response.status_code == 200
    payload = response.json()
    assert payload["tool"] == "text.uppercase"
    assert payload["result"]["result"] == "UPPERCASE THIS"
