from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from modules.manager import module as manager_module
from modules.text_module import module as text_module


class DummyCore:
    pass


def _build_app() -> tuple[FastAPI, TestClient]:
    core = DummyCore()
    app = FastAPI()
    manager = manager_module.Module(core)
    text = text_module.Module(core)
    app.include_router(manager.get_router())
    app.include_router(text.get_router())
    client = TestClient(app)
    return app, client


def test_manager_run_executes_uppercase(monkeypatch):
    _, client = _build_app()

    data_dir = Path(__file__).resolve().parents[1] / "data"
    monkeypatch.setattr(manager_module.settings, "data_dir", str(data_dir))

    class DummyHTTPXClient:
        def __init__(self, *args, **kwargs):
            self._enter = False

        def __enter__(self):
            self._enter = True
            return self

        def __exit__(self, exc_type, exc, tb):
            self._enter = False

        def get(self, url, params=None):
            assert self._enter
            path = url.split("/", 3)
            if len(path) >= 4:
                endpoint = "/" + path[3]
            else:
                endpoint = url
            return client.get(endpoint, params=params)

        def post(self, url, params=None, json=None):
            assert self._enter
            path = url.split("/", 3)
            if len(path) >= 4:
                endpoint = "/" + path[3]
            else:
                endpoint = url
            return client.post(endpoint, params=params, json=json)

    monkeypatch.setattr(manager_module, "httpx", type("_DummyHTTPX", (), {"Client": DummyHTTPXClient}))

    response = client.post("/manager/run", json={"goal": "uppercase hello"})
    payload = response.json()

    assert response.status_code == 200
    assert payload["tool"] == "text.uppercase"
    assert payload["query"] == {"s": "uppercase hello"}
    assert payload["result"] == {"result": "UPPERCASE HELLO"}
