from __future__ import annotations
import asyncio, json, threading, time
import httpx
from fastapi import Body
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import httpx, json

from coman.core.base_module import BaseModule
from coman.core.config import settings


def _normalize_result(res):
    # если внутри строка с JSON — распарсим; если просто текст — вернём текст
    if isinstance(res, str):
        s = res.strip()
        if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
            s = s[1:-1]
        try:
            return json.loads(s)
        except Exception:
            return s
    return res


class Module(BaseModule):
    name = "telegram"
    description = "Telegram bot bridge"

    def __init__(self, core):
        super().__init__(core)
        self.app: Application | None = None
        self._th: threading.Thread | None = None
        self._stop = threading.Event()

        @self.router.get("/status")
        def status():
            return {
                "configured": bool(settings.telegram_bot_token),
                "running": bool(self._th and self._th.is_alive()),
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
            try:
                if self.app and getattr(self, "_loop", None):
                    self._loop.call_soon_threadsafe(lambda: asyncio.create_task(self.app.stop()))
            except Exception:
                pass
            return {"stopped": True}

    def _runner(self):
        # создаём event loop в потоке, чтобы не было "There is no current event loop"
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
            text = (update.message.text or "").strip()

            # 1) формируем payload для /manager/run
            try:
                if text.startswith("{"):
                    payload = json.loads(text)          # пользователь прислал JSON → шлём как body
                else:
                    payload = {"goal": text}            # обычный текст → goal
            except Exception:
                payload = {"goal": text}

            # 2) вызываем менеджер
            try:
                async with httpx.AsyncClient(timeout=20) as c:
                    r = await c.post(f"{settings.api_base}/manager/run", json=payload)
                    try:
                        data = r.json()
                    except Exception:
                        data = {"result": r.text}
            except Exception as e:
                await update.message.reply_text(f"error: {e}")
                return

            res = data.get("result", data)
            res = _normalize_result(res)

            # 3) красиво отвечаем
            if isinstance(res, (dict, list)):
                out = json.dumps(res, ensure_ascii=False, indent=2)
            else:
                out = str(res)

            await update.message.reply_text(out)

        # строим приложение и запускаем polling
        self.app = Application.builder().token(settings.telegram_bot_token).build()
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

        self._loop.run_until_complete(self.app.initialize())
        self._loop.run_until_complete(self.app.start())
        try:
            while not self._stop.is_set():
                time.sleep(0.2)
        finally:
            self._loop.run_until_complete(self.app.stop())
            self._loop.run_until_complete(self.app.shutdown())
            self._loop.close()



