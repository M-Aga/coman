import asyncio

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "telegram"))

from telegram.coman.modules.telegram_module.db import DB
from telegram.coman.modules.telegram_module import handlers


def test_db_respects_default_language(tmp_path):
    db_path = tmp_path / "users.db"
    db = DB(str(db_path), default_lang="EN")

    assert db.upsert_user(1, "alice") is True
    assert db.get_language(1) == "en"

    db.set_language(1, "ru")
    assert db.upsert_user(1, "alice") is False
    assert db.get_language(1) == "ru"


def test_format_dict_renders_nested_structures():
    data = {
        "version": "1.0",
        "workers": {"active": 2},
        "features": ["a", "b"],
    }

    text = handlers._format_dict(data)

    assert "version" in text
    assert "workers" in text
    assert "active" in text
def test_render_status_combines_health_and_info():
    class DummyAPI:
        def __init__(self, health, info):
            self._health = health
            self._info = info

        def health(self):
            return self._health

        def info(self):
            return self._info

    api = DummyAPI(
        {"status": "ok", "workers": {"alive": 3}},
        {"version": "2.1.0", "uptime": "5m"},
    )

    text = asyncio.run(handlers._render_status(api, "en"))

    assert "Core service is reachable" in text
    assert "version" in text


def test_render_status_reports_errors():
    class DummyAPI:
        def health(self):
            return {"error": "boom"}

        def info(self):
            return {}

    text = asyncio.run(handlers._render_status(DummyAPI(), "en"))

    assert "boom" in text
