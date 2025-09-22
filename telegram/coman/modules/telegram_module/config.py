import os
from dataclasses import dataclass
from typing import List

def _parse_admin_ids(value: str) -> List[int]:
    ids = []
    for part in (value or "").replace(";", ",").split(","):
        part = part.strip()
        if not part:
            continue
        try:
            ids.append(int(part))
        except ValueError:
            pass
    return ids

@dataclass
class Config:
    # Required
    telegram_token: str

    # Optional
    db_path: str = os.getenv("COMAN_TG_DB_PATH", "bot_users.db")
    default_lang: str = os.getenv("COMAN_TG_DEFAULT_LANG", "ru")
    admin_ids: List[int] = None
    api_base_url: str = os.getenv("COMAN_API_BASE_URL", "http://localhost:8000")
    api_token: str = os.getenv("COMAN_API_TOKEN", "")
    request_timeout_s: int = int(os.getenv("COMAN_API_TIMEOUT_S", "12"))

    def __post_init__(self):
        if self.admin_ids is None:
            self.admin_ids = _parse_admin_ids(os.getenv("TELEGRAM_ADMIN_IDS", ""))

def load_config() -> "Config":
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Env TELEGRAM_BOT_TOKEN is required")
    return Config(telegram_token=token)
