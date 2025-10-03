from __future__ import annotations

from fastapi.testclient import TestClient


class DummyCore:
    def __init__(self):
        self.modules = {}
        self.scheduler = None


def test_build_fastapi_app_defers_scheduler_start(monkeypatch):
    from core import app as core_app

    calls: list[str] = []

    class DummyScheduler:
        def __init__(self):
            calls.append("init")

        def start(self) -> None:
            calls.append("start")

        def shutdown(self) -> None:
            calls.append("shutdown")

    monkeypatch.setattr(core_app, "Scheduler", DummyScheduler)
    monkeypatch.setattr(core_app, "mount_ui", lambda _app: None)

    core = DummyCore()
    application = core_app.build_fastapi_app(core)

    assert calls == ["init"]
    assert isinstance(core.scheduler, DummyScheduler)

    with TestClient(application) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "modules": []}

    assert calls == ["init", "start", "shutdown"]
