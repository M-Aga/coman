# Lightweight i18n without external gettext runtime.
# You can extend this dictionary or wire real gettext later.
from typing import Dict

_STRINGS: Dict[str, Dict[str, str]] = {
    "ru": {
        "welcome": "Добро пожаловать! Выберите действие из меню:",
        "btn_get_data": "Получить данные",
        "btn_send_data": "Отправить данные",
        "btn_about": "О боте",
        "btn_settings": "Настройки",
        "btn_admin": "Админ-панель",
        "enter_text": "Введите текст, который хотите отправить:",
        "sent_ok": "Данные успешно отправлены!",
        "send_err": "Ошибка при отправке данных",
        "fetch_err": "Ошибка при получении данных",
        "data_from_api": "Данные из API",
        "about_text": "Этот бот — модуль Telegram проекта Coman.\nВерсия: o1\nРоль: интерфейс к ядру/оркестратору.",
        "settings": "Настройки:",
        "lang_ru": "Русский",
        "lang_en": "English",
        "back": "Назад",
        "lang_changed": "Язык изменён!",
        "choose_menu": "Пожалуйста, выберите действие из меню (/start).",
        "admin_welcome": "Добро пожаловать в админ-панель. Здесь можно управлять пользователями и интеграциями.",
        "not_authorized": "Недостаточно прав для выполнения действия.",
    },
    "en": {
        "welcome": "Welcome! Choose an action from the menu:",
        "btn_get_data": "Get data",
        "btn_send_data": "Send data",
        "btn_about": "About",
        "btn_settings": "Settings",
        "btn_admin": "Admin Panel",
        "enter_text": "Type the text you want to send:",
        "sent_ok": "Data sent successfully!",
        "send_err": "Error sending data",
        "fetch_err": "Error fetching data",
        "data_from_api": "Data from API",
        "about_text": "This bot is the Telegram module of the Coman project.\nVersion: o1\nRole: interface to the core/orchestrator.",
        "settings": "Settings:",
        "lang_ru": "Русский",
        "lang_en": "English",
        "back": "Back",
        "lang_changed": "Language changed!",
        "choose_menu": "Please choose an action from the menu (/start).",
        "admin_welcome": "Welcome to the admin panel. You can manage users and integrations here.",
        "not_authorized": "You are not authorized to perform this action.",
    }
}

def t(lang: str, key: str) -> str:
    lang = (lang or "ru").lower()
    if lang not in _STRINGS:
        lang = "en"
    table = _STRINGS[lang]
    return table.get(key, _STRINGS["en"].get(key, key))
