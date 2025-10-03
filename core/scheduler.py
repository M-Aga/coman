from __future__ import annotations

import logging

try:  # pragma: no cover - optional dependency
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
except Exception:  # pragma: no cover - graceful fallback when apscheduler is missing
    AsyncIOScheduler = None  # type: ignore[assignment]
    CronTrigger = None  # type: ignore[assignment]


log = logging.getLogger("coman.scheduler")


class Scheduler:
    def __init__(self):
        if AsyncIOScheduler is None:
            self.scheduler = None
            log.warning(
                "apscheduler is not installed; background schedules will be skipped."
            )
        else:
            self.scheduler = AsyncIOScheduler()

    def start(self):
        if self.scheduler is not None:
            self.scheduler.start()

    def shutdown(self):
        if self.scheduler is not None:
            try:
                self.scheduler.shutdown(wait=False)
            except Exception:
                log.debug("Failed to shutdown scheduler cleanly", exc_info=True)

    def add_cron(self, func, cron: str, name: str):
        if self.scheduler is None or CronTrigger is None:
            log.debug("Skipping cron job '%s' because scheduler is unavailable", name)
            return
        self.scheduler.add_job(func, CronTrigger.from_crontab(cron), name=name)
