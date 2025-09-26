import os


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


class Settings:
    def __init__(self):
        self.env = os.getenv("COMAN_ENV", "dev")
        self.log_level = os.getenv("COMAN_LOG_LEVEL", "INFO")
        self.data_dir = os.getenv("COMAN_DATA_DIR", "./coman/data")
        self.api_base = os.getenv("COMAN_API_BASE", "http://127.0.0.1:8000")
        self.allowed_integration_paths = _split_paths(os.getenv("COMAN_ALLOWED_INTEGRATION_PATHS", "./integrations,."))
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.openrouter_base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")


settings = Settings()
