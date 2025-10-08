# Coman Telegram Service

This directory contains the standalone Telegram bot runner that ships with the
Coman platform.  The service is also exposed through the unified CLI so you can
launch it with ``python -m coman.modules.main telegram`` (or via ``run_coman.bat``
on Windows).

## Prerequisites

* Python 3.10+
* Telegram bot token (create one via @BotFather)
* Optional: a local SQLite database path for storing user profiles

Install the dependencies alongside the rest of the project:

```bash
pip install -r modules/requirements.txt
```

## Configuration

Create a ``.env`` file next to this README and populate the variables:

```
TELEGRAM_BOT_TOKEN=1234567890:ABCDEF
TELEGRAM_ADMIN_IDS=12345,67890
COMAN_API_BASE_URL=http://localhost:8000
COMAN_API_TIMEOUT_S=12
COMAN_TG_DB_PATH=bot_users.db
COMAN_TG_DEFAULT_LANG=ru
```

## Running the bot

* **Via the unified CLI:**
  ```bash
  python -m coman.modules.main telegram
  ```
* **Direct execution:**
  ```bash
  python telegram/main.py
  ```
* **Windows helper:** execute ``run_coman.bat telegram``

The runner will reuse the FastAPI client utilities defined in the core package
so the bot can query the HTTP API for integration data.

## Example prompts and flows

Once the bot is running you can message it directly in Telegram. The commands
and inline buttons exposed by the handlers cover the following common flows:

* **Show the main menu:** send `/start` to register the user, reset any pending
  flows, and display the interactive menu with actions such as “Get data”,
  “Send data”, “System status”, “About”, “Settings”, and optionally “Admin
  Panel” for privileged users.
* **Get the current status:** tap the “System status” button or send `/status`
  to trigger the status handler. The bot fetches the latest health and info data
  from the Coman API and returns a formatted summary.
* **Submit text for processing:** choose “Send data” from the menu. The bot will
  prompt you with “Type the text you want to send:” and wait for your next
  message. Reply with the payload you want to forward to the Coman API; the bot
  echoes either a success confirmation or the error returned by the service.
* **Retrieve information:** pick “Get data” to ask the API for the structured
  info payload and display it in chat using bullet points.
* **Adjust language:** open “Settings” and select either “Русский” or
  “English”. The preference is stored per user and subsequent prompts adopt the
  chosen language.
* **Reach the admin panel:** if the user ID matches the configured admin list or
  a stored admin role, pressing “Admin Panel” shows the dedicated welcome text
  and can be extended with privileged actions.

These prompts mirror the logic implemented in
`telegram/coman/modules/telegram_module/handlers.py`, so they stay in sync with
the shipped bot behaviour.

## Docker usage

```bash
docker build -t coman-telegram:latest telegram/
docker run --rm -it --env-file telegram/.env coman-telegram:latest
```

Mount a volume for ``bot_users.db`` if you want to persist the SQLite data:

```bash
docker run --rm -it --env-file telegram/.env \
  -v $(pwd)/telegram/bot_users.db:/app/bot_users.db \
  coman-telegram:latest
```

## Troubleshooting

* **401 from the API** – double check the API base URL and authentication
  headers configured in ``telegram/config.py``.
* **Module import errors** – ensure you installed dependencies and that the
  project root is on ``PYTHONPATH`` (this is handled automatically when running
  through the CLI).  The bundled ``telegram`` package is a shim that expects the
  upstream ``python-telegram-bot`` distribution to be installed.

