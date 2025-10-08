from __future__ import annotations

import asyncio
import threading
import time
from typing import Any

from fastapi import Body

from coman.core.base_module import BaseModule
from coman.core.config import settings
from telegram.coman.modules.telegram_module.bot import build_application
from telegram.coman.modules.telegram_module.config import Config


class Module(BaseModule):
    name = "telegram"
    description = "Telegram bot bridge"

    def __init__(self, core):
        super().__init__(core)
        self.app: Any | None = None
        self._th: threading.Thread | None = None
        self._stop = threading.Event()

        @self.router.get("/status")
        def status():
            token = settings.telegram_bot_token
            return {
                "configured": bool(token),
                "running": bool(self._th and self._th.is_alive()),
                "source": getattr(settings, "telegram_token_source", "env" if token else "none"),
                "token_tail": token[-4:] if token else "",
            }

        @self.router.post("/start")
        def start():
            if not settings.telegram_bot_token:
                return {"started": False, "error": "no_token"}
            if self._th and self._th.is_alive():
                return {"started": True, "already": True}
            self._stop.clear()
            self._th = threading.Thread(target=self._runner, daemon=True)
            self._th.start()
            return {"started": True}

        @self.router.post("/stop")
        def stop():
            self._stop.set()
            if self.app and getattr(self, "_loop", None):
                try:
                    self._loop.call_soon_threadsafe(lambda: asyncio.create_task(self.app.stop()))
                except Exception:  # pragma: no cover - defensive guard
                    pass
            return {"stopped": True}

        @self.router.post("/token")
        def set_token(token: str = Body("", embed=True)):
            settings.store_telegram_bot_token(token)
            current = settings.telegram_bot_token
            return {
                "configured": bool(current),
                "source": getattr(settings, "telegram_token_source", "env" if current else "none"),
                "token_tail": current[-4:] if current else "",
            }

    def _runner(self):
        # создаём event loop в потоке, чтобы не было "There is no current event loop"
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        cfg = Config(telegram_token=settings.telegram_bot_token, api_base_url=settings.api_base)
        self.app = build_application(cfg)

        async def _start() -> None:
            await self.app.initialize()
            await self.app.start()
            updater = getattr(self.app, "updater", None)
            if updater and hasattr(updater, "start_polling"):
                result = updater.start_polling()
                if asyncio.iscoroutine(result):  # pragma: no cover - depends on telegram version
                    await result

        self._loop.run_until_complete(_start())
        try:
            while not self._stop.is_set():
                time.sleep(0.2)
        finally:
            async def _shutdown() -> None:
                updater = getattr(self.app, "updater", None)
                if updater and hasattr(updater, "stop"):
                    result = updater.stop()
                    if asyncio.iscoroutine(result):  # pragma: no cover - depends on telegram version
                        await result
                await self.app.stop()
                await self.app.shutdown()

            self._loop.run_until_complete(_shutdown())
            self._loop.close()
