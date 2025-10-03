from __future__ import annotations

from fastapi import FastAPI
from fastapi.dependencies import utils as fastapi_utils
from fastapi.testclient import TestClient

from modules.ui.mount import mount_ui


def test_ui_index_template_renders_from_filesystem(monkeypatch):
    monkeypatch.setattr(fastapi_utils, "ensure_multipart_is_installed", lambda: None)
    app = FastAPI()
    mount_ui(app)

    with TestClient(app) as client:
        response = client.get("/ui")

    assert response.status_code == 200
    assert "Coman" in response.text
