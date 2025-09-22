from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from .db import DB
from .i18n import t
from .api import ComanAPI

def _is_admin(user_id: int, db: DB, admin_ids: list[int]) -> bool:
    return user_id in set(admin_ids or []) or db.get_role(user_id) == "admin"

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE, db: DB, admins: list[int]):
    user = update.effective_user
    db.upsert_user(user.id, user.username)
    lang = db.get_language(user.id)

    keyboard = [
        [InlineKeyboardButton(t(lang, "btn_get_data"), callback_data="menu:get_data")],
        [InlineKeyboardButton(t(lang, "btn_send_data"), callback_data="menu:send_data")],
        [InlineKeyboardButton(t(lang, "btn_about"), callback_data="menu:about")],
        [InlineKeyboardButton(t(lang, "btn_settings"), callback_data="menu:settings")],
    ]

    if _is_admin(user.id, db, admins):
        keyboard.append([InlineKeyboardButton(t(lang, "btn_admin"), callback_data="menu:admin")])

    await update.message.reply_text(
        t(lang, "welcome"),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def cb_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, db: DB, api: ComanAPI, admins: list[int]):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    lang = db.get_language(user.id)

    data = (query.data or "").split(":")
    action = data[1] if len(data) > 1 else ""

    if action == "get_data":
        # Example: GET /v1/info
        resp = api.info()
        if "error" in resp:
            await query.edit_message_text(f"{t(lang,'fetch_err')}: {resp['error']}")
        else:
            await query.edit_message_text(f"{t(lang,'data_from_api')}: {resp}")
    elif action == "send_data":
        await query.edit_message_text(t(lang, "enter_text"))
        context.user_data["awaiting_input"] = True
    elif action == "about":
        await query.edit_message_text(t(lang, "about_text"))
    elif action == "settings":
        keyboard = [
            [InlineKeyboardButton(t(lang, "lang_ru"), callback_data="settings:lang:ru")],
            [InlineKeyboardButton(t(lang, "lang_en"), callback_data="settings:lang:en")],
            [InlineKeyboardButton(t(lang, "back"), callback_data="menu:back")],
        ]
        await query.edit_message_text(
            t(lang, "settings"),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    elif action == "admin":
        if not _is_admin(user.id, db, admins):
            await query.edit_message_text(t(lang, "not_authorized"))
            return
        await query.edit_message_text(t(lang, "admin_welcome"))
    elif action == "back":
        # redraw menu
        keyboard = [
            [InlineKeyboardButton(t(lang, "btn_get_data"), callback_data="menu:get_data")],
            [InlineKeyboardButton(t(lang, "btn_send_data"), callback_data="menu:send_data")],
            [InlineKeyboardButton(t(lang, "btn_about"), callback_data="menu:about")],
            [InlineKeyboardButton(t(lang, "btn_settings"), callback_data="menu:settings")],
        ]
        if _is_admin(user.id, db, admins):
            keyboard.append([InlineKeyboardButton(t(lang, "btn_admin"), callback_data="menu:admin")])
        await query.edit_message_text(t(lang, "welcome"), reply_markup=InlineKeyboardMarkup(keyboard))

async def cb_settings(update: Update, context: ContextTypes.DEFAULT_TYPE, db: DB):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    lang = db.get_language(user.id)

    data = (query.data or "").split(":")
    if len(data) >= 3 and data[1] == "lang":
        new_lang = data[2]
        db.set_language(user.id, new_lang)
        # Update inline with confirmation
        await query.edit_message_text(t(new_lang, "lang_changed"))

async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE, db: DB, api: ComanAPI):
    user = update.effective_user
    lang = db.get_language(user.id)

    if context.user_data.get("awaiting_input"):
        context.user_data["awaiting_input"] = False
        text = update.message.text or ""
        # Example: POST /v1/process_text
        resp = api.process_text(text)
        if "error" in resp:
            await update.message.reply_text(f"{t(lang,'send_err')}: {resp['error']}")
        else:
            await update.message.reply_text(t(lang, "sent_ok"))
    else:
        await update.message.reply_text(t(lang, "choose_menu"))
