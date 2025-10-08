from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


_STUB_PACKAGE_NAME = "_fastapi_stub_pkg"


def _load_stub_module(name: str, relative_path: str) -> ModuleType:
    root = Path(__file__).resolve().parents[1] / "fastapi"
    path = root / relative_path
    package = sys.modules.get(_STUB_PACKAGE_NAME)
    if package is None:
        package = ModuleType(_STUB_PACKAGE_NAME)
        package.__path__ = [str(root)]  # type: ignore[attr-defined]
        sys.modules[_STUB_PACKAGE_NAME] = package

    full_name = f"{_STUB_PACKAGE_NAME}.{name}"
    spec = importlib.util.spec_from_file_location(full_name, path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise RuntimeError(f"Unable to load stub module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[full_name] = module
    spec.loader.exec_module(module)
    return module


def test_stub_testclient_supports_context_manager() -> None:
    _load_stub_module("exceptions", "exceptions.py")
    _load_stub_module("params", "params.py")
    _load_stub_module("routing", "routing.py")
    app_module = _load_stub_module("app", "app.py")
    testclient_module = _load_stub_module("testclient", "testclient.py")

    app = app_module.FastAPI()
    app.add_api_route("/ping", lambda: {"pong": True}, methods=["GET"])

    with testclient_module.TestClient(app) as client:
        response = client.get("/ping")

    assert response.status_code == 200
    assert response.json() == {"pong": True}
