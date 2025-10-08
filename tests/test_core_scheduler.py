from __future__ import annotations

import pytest

from core import scheduler


def test_scheduler_wraps_asyncio_scheduler(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []

    class FakeScheduler:
        def start(self) -> None:
            events.append("start")

        def shutdown(self, wait: bool = False) -> None:
            events.append(f"shutdown:{wait}")

        def add_job(self, func, trigger, name: str):
            events.append(f"job:{name}:{trigger}")

    class FakeTrigger:
        @staticmethod
        def from_crontab(expr: str) -> str:
            return f"cron:{expr}"

    monkeypatch.setattr(scheduler, "AsyncIOScheduler", FakeScheduler)
    monkeypatch.setattr(scheduler, "CronTrigger", FakeTrigger)

    sched = scheduler.Scheduler()
    sched.start()
    sched.add_cron(lambda: None, "*/5 * * * *", name="heartbeat")
    sched.shutdown()

    assert events == ["start", "job:heartbeat:cron:*/5 * * * *", "shutdown:False"]


def test_scheduler_noop_when_dependency_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(scheduler, "AsyncIOScheduler", None)
    monkeypatch.setattr(scheduler, "CronTrigger", None)

    sched = scheduler.Scheduler()
    sched.start()
    sched.add_cron(lambda: None, "* * * * *", name="noop")
    sched.shutdown()
