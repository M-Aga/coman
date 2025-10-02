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
  through the CLI).
