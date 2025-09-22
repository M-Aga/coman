import logging
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters
)
from .config import load_config
from .db import DB
from .api import ComanAPI
from .handlers import cmd_start, cb_menu, cb_settings, on_text

log = logging.getLogger("coman.telegram")

def build_application():
    cfg = load_config()
    db = DB(cfg.db_path)
    api = ComanAPI(cfg.api_base_url, cfg.api_token, cfg.request_timeout_s)

    application = ApplicationBuilder().token(cfg.telegram_token).build()

    # Wrap handlers to inject dependencies without global state
    async def start(update, context):
        return await cmd_start(update, context, db=db, admins=cfg.admin_ids)

    async def menu(update, context):
        return await cb_menu(update, context, db=db, api=api, admins=cfg.admin_ids)

    async def settings(update, context):
        return await cb_settings(update, context, db=db)

    async def text(update, context):
        return await on_text(update, context, db=db, api=api)

    # Register
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", start))
    application.add_handler(CommandHandler("help", start))
    application.add_handler(CallbackQueryHandler(menu, pattern=r"^menu:"))
    application.add_handler(CallbackQueryHandler(settings, pattern=r"^settings:"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text))

    return application

def run():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    app = build_application()
    log.info("Starting Telegram bot (o1)...")
    app.run_polling(close_loop=False)
