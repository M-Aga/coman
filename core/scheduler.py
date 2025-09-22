from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
class Scheduler:
    def __init__(self): self.scheduler = AsyncIOScheduler()
    def start(self): self.scheduler.start()
    def add_cron(self, func, cron: str, name: str):
        self.scheduler.add_job(func, CronTrigger.from_crontab(cron), name=name)
