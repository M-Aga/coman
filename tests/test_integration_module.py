from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from coman.core.registry import Core
from coman.modules.integration import module as integration_module
from coman.modules.integration.module import Module


def _make_client(tmp_path, monkeypatch) -> TestClient:
    tmp_path.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(integration_module.settings, "data_dir", str(tmp_path), raising=False)
    allowed = [str(Path(__file__).resolve().parents[2])]
    monkeypatch.setattr(integration_module.settings, "allowed_integration_paths", allowed, raising=False)
    core = Core()
    mod = Module(core)
    app = FastAPI()
    app.include_router(mod.get_router())
    return TestClient(app)


def _register_sample(client: TestClient, base_path: Path) -> None:
    resp = client.post(
        "/integration/register",
        params={
            "name": "sample",
            "path": str(base_path),
            "module": "tests.sample_integration",
            "callable": "run",
        },
    )
    assert resp.status_code == 200, resp.text


def test_call_uses_registered_module(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)
    base_path = Path(__file__).resolve().parents[2]
    _register_sample(client, base_path)

    resp = client.post(
        "/integration/call",
        params={"name": "sample"},
        json={"kwargs": {"value": 42}},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["result"] == {"received": {"value": 42}}

    resp = client.post(
        "/integration/call",
        params={"name": "sample", "callable": "run"},
        json={"kwargs": {"value": 99}},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["result"] == {"received": {"value": 99}}


def test_call_rejects_foreign_module(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)
    base_path = Path(__file__).resolve().parents[2]
    _register_sample(client, base_path)

    resp = client.post(
        "/integration/call",
        params={"name": "sample", "callable": "os.system"},
        json={"kwargs": {}},
    )
    assert resp.status_code == 400
    assert "registered module" in resp.json()["detail"]
