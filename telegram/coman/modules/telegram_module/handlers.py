import asyncio
import json
from typing import Any, Dict

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from .db import DB
from .i18n import t
from .api import ComanAPI

def _is_admin(user_id: int, db: DB, admin_ids: list[int]) -> bool:
    return user_id in set(admin_ids or []) or db.get_role(user_id) == "admin"


def _main_menu(lang: str, is_admin: bool) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(t(lang, "btn_get_data"), callback_data="menu:get_data")],
        [InlineKeyboardButton(t(lang, "btn_send_data"), callback_data="menu:send_data")],
        [InlineKeyboardButton(t(lang, "btn_status"), callback_data="menu:status")],
        [InlineKeyboardButton(t(lang, "btn_about"), callback_data="menu:about")],
        [InlineKeyboardButton(t(lang, "btn_settings"), callback_data="menu:settings")],
    ]
    if is_admin:
        keyboard.append([InlineKeyboardButton(t(lang, "btn_admin"), callback_data="menu:admin")])
    return InlineKeyboardMarkup(keyboard)


def _back_markup(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton(t(lang, "back"), callback_data="menu:back")]])


def _format_dict(data: Dict[str, Any]) -> str:
    lines: list[str] = []
    for key, value in data.items():
        if isinstance(value, (dict, list)):
            pretty = json.dumps(value, ensure_ascii=False, indent=2)
            lines.append(f"• {key}:\n{pretty}")
        else:
            lines.append(f"• {key}: {value}")
    return "\n".join(lines)


async def _call_api(func, *args, **kwargs) -> Dict[str, Any]:
    return await asyncio.to_thread(func, *args, **kwargs)


async def cmd_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    db: DB,
    admins: list[int],
    help_only: bool = False,
):
    user = update.effective_user
    is_new = db.upsert_user(user.id, user.username)
    lang = db.get_language(user.id)
    is_admin = _is_admin(user.id, db, admins)

    # Reset pending flows when user re-opens the menu/help.
    context.user_data.pop("awaiting_input", None)

    if help_only:
        text = "\n\n".join(filter(None, [t(lang, "help_text"), t(lang, "menu_hint")]))
    else:
        welcome_key = "welcome_new" if is_new else "welcome_back"
        text = "\n\n".join(filter(None, [t(lang, welcome_key), t(lang, "menu_hint")]))

    reply_markup = _main_menu(lang, is_admin)
    message = update.effective_message
    if message:
        await message.reply_text(text, reply_markup=reply_markup)
    else:
        await update.effective_chat.send_message(text, reply_markup=reply_markup)


async def _render_status(api: ComanAPI, lang: str) -> str:
    health = await _call_api(api.health)
    if not health:
        return "\n".join([t(lang, "status_title"), t(lang, "status_no_details")])
    if "error" in health:
        return t(lang, "status_error").format(error=health["error"])

    lines = [t(lang, "status_title"), t(lang, "status_ok")]
    state = health.get("status") or health.get("state")
    if state:
        lines.append(f"• {t(lang, "status_health")}: {state}")
    details = {k: v for k, v in health.items() if k not in {"status", "state"}}
    if details:
        lines.append(t(lang, "status_details"))
        lines.append(_format_dict(details))

    info = await _call_api(api.info)
    if info:
        if "error" in info:
            lines.append("\n" + t(lang, "status_info_error").format(error=info["error"]))
        elif info:
            lines.append("\n".join(["", t(lang, "status_info_title"), _format_dict(info)]))
    return "\n".join(lines)


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE, db: DB, api: ComanAPI):
    user = update.effective_user
    db.upsert_user(user.id, user.username)
    lang = db.get_language(user.id)
    status_text = await _render_status(api, lang)
    markup = _back_markup(lang)
    message = update.effective_message
    if message:
        await message.reply_text(status_text, reply_markup=markup)
    else:
        await update.effective_chat.send_message(status_text, reply_markup=markup)


async def cb_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, db: DB, api: ComanAPI, admins: list[int]):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    lang = db.get_language(user.id)

    data = (query.data or "").split(":")
    action = data[1] if len(data) > 1 else ""

    if action == "get_data":
        resp = await _call_api(api.info)
        if not resp:
            await query.edit_message_text(t(lang, "no_data"), reply_markup=_back_markup(lang))
        elif "error" in resp:
            await query.edit_message_text(f"{t(lang,'fetch_err')}: {resp['error']}", reply_markup=_back_markup(lang))
        else:
            formatted = _format_dict(resp)
            await query.edit_message_text(
                "\n".join([t(lang, "data_from_api"), formatted or t(lang, "no_data")]),
                reply_markup=_back_markup(lang),
            )
    elif action == "send_data":
        await query.edit_message_text(t(lang, "enter_text"))
        context.user_data["awaiting_input"] = True
    elif action == "about":
        await query.edit_message_text(t(lang, "about_text"), reply_markup=_back_markup(lang))
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
        await query.edit_message_text(t(lang, "admin_welcome"), reply_markup=_back_markup(lang))
    elif action == "status":
        status_text = await _render_status(api, lang)
        await query.edit_message_text(status_text, reply_markup=_back_markup(lang))
    elif action == "back":
        # redraw menu
        back_text = "\n\n".join(filter(None, [t(lang, "welcome_back"), t(lang, "menu_hint")]))
        await query.edit_message_text(back_text, reply_markup=_main_menu(lang, _is_admin(user.id, db, admins)))

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
        resp = await _call_api(api.process_text, text)
        if "error" in resp:
            await update.message.reply_text(f"{t(lang,'send_err')}: {resp['error']}")
        else:
            details = resp.get("result") or resp.get("message")
            if details:
                await update.message.reply_text("\n".join([t(lang, "sent_ok"), f"{t(lang, 'response_details')}: {details}"]))
            else:
                await update.message.reply_text(t(lang, "sent_ok"))
    else:
        await update.message.reply_text("\n".join([t(lang, "choose_menu"), t(lang, "menu_hint")]))
