import os
from pathlib import Path


def _split_paths(val: str):
    parts = [p.strip() for p in (val or "").split(",") if p.strip()]
    if not parts:
        cwd = os.getcwd()
        parts = [cwd, os.path.join(cwd, "integrations"), "."]
    norm = []
    for p in parts:
        ap = os.path.abspath(p)
        if ap not in norm:
            norm.append(ap)
    return norm


_DEFAULT_DATA_DIR = Path(__file__).resolve().parents[1] / "data"


class Settings:
    def __init__(self):
        self.env = os.getenv("COMAN_ENV", "dev")
        self.log_level = os.getenv("COMAN_LOG_LEVEL", "INFO")
        default_data_dir = str(_DEFAULT_DATA_DIR)
        self.data_dir = os.getenv("COMAN_DATA_DIR", default_data_dir)
        self.api_base = os.getenv("COMAN_API_BASE", "http://127.0.0.1:8000")
        self.allowed_integration_paths = _split_paths(os.getenv("COMAN_ALLOWED_INTEGRATION_PATHS", "./integrations,."))
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.openrouter_base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

        self._telegram_token_file = os.path.join(self.data_dir, "telegram_token.txt")
        env_token_raw = os.getenv("TELEGRAM_BOT_TOKEN")
        self._telegram_env_token = env_token_raw.strip() if env_token_raw else ""
        if self._telegram_env_token:
            self.telegram_bot_token = self._telegram_env_token
            self.telegram_token_source = "env"
        else:
            self.telegram_bot_token = self._load_telegram_token_from_disk()
            self.telegram_token_source = "file" if self.telegram_bot_token else "none"

    def _load_telegram_token_from_disk(self) -> str:
        try:
            with open(self._telegram_token_file, "r", encoding="utf-8") as fh:
                return fh.read().strip()
        except FileNotFoundError:
            return ""
        except OSError:
            return ""

    def store_telegram_bot_token(self, token: str) -> None:
        token = (token or "").strip()
        os.makedirs(self.data_dir, exist_ok=True)

        if token:
            with open(self._telegram_token_file, "w", encoding="utf-8") as fh:
                fh.write(token)
            self.telegram_bot_token = token
            self.telegram_token_source = "file"
        else:
            try:
                os.remove(self._telegram_token_file)
            except FileNotFoundError:
                pass
            except OSError:
                pass

            if self._telegram_env_token:
                self.telegram_bot_token = self._telegram_env_token
                self.telegram_token_source = "env"
            else:
                self.telegram_bot_token = ""
                self.telegram_token_source = "none"


settings = Settings()
