# Coman Telegram Module (o1)

Готовый к запуску модуль Telegram для проекта **Coman**. Простая, надёжная архитектура (модель **o1**): без лишних зависимостей, с понятной структурой и точками интеграции с ядром/оркестратором Coman через REST API.

## Возможности
- Многоуровневое меню (inline-кнопки)
- Хранение пользователей (SQLite): язык, роль, username
- Роли: `user`, `admin` (админы — из БД или через `TELEGRAM_ADMIN_IDS`)
- Простая локализация (RU/EN) без внешних `.po/.mo`
- Интеграция с ядром через REST (`/v1/info`, `/v1/process_text`, `/health`)
- Готов к **Docker**

## Быстрый старт (локально)
1. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
2. Скопируйте `.env.example` в `.env` и заполните `TELEGRAM_BOT_TOKEN`:
   ```bash
   cp .env.example .env
   # отредактируйте .env
   ```
3. Экспортируйте переменные окружения (или используйте dotenv-настройку вашей среды):
   ```bash
   export $(grep -v '^#' .env | xargs)
   ```
4. Запустите:
   ```bash
   python main.py
   ```

## Docker
```bash
docker build -t coman-telegram-o1:latest .
docker run --rm -it \
  --env-file .env \
  -v $(pwd)/bot_users.db:/app/bot_users.db \
  coman-telegram-o1:latest
```

## Конфигурация (переменные окружения)
- `TELEGRAM_BOT_TOKEN` — **обязателен**
- `TELEGRAM_ADMIN_IDS` — список ID админов (через `,` или `;`)
- `COMAN_API_BASE_URL` — URL ядра/оркестратора Coman (по умолчанию `http://localhost:8000`)
- `COMAN_API_TOKEN` — токен доступа к API (если нужен)
- `COMAN_API_TIMEOUT_S` — таймаут запросов (секунды, по умолчанию 12)
- `COMAN_TG_DB_PATH` — путь к SQLite базе (`bot_users.db`)
- `COMAN_TG_DEFAULT_LANG` — язык по умолчанию (`ru`)

## Точки интеграции
- Реальные эндпоинты замените в `coman/modules/telegram_module/api.py`
- При необходимости подключите ваши модули в `handlers.py` и вызывайте их внутри `on_text`/`cb_menu`

## Команды
- `/start`, `/menu`, `/help` — открыть главное меню
- Меню: **Получить данные**, **Отправить данные**, **О боте**, **Настройки**, **Админ-панель** (для админов)

## Миграции БД
Первая загрузка автоматически создаёт таблицу `users`.

## Примечания
- Модуль использует `python-telegram-bot v21` (асинхронные обработчики, но простой запуск).
- При высокой нагрузке можно вынести БД и API-клиент в отдельные сервисы, а также добавить кэш.
