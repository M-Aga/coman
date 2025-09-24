import sqlite3
from typing import Optional

class DB:
    def __init__(self, path: str, default_lang: str = "ru"):
        self.path = path
        self.default_lang = (default_lang or "ru").lower()
        self._init()

    def _connect(self):
        # check_same_thread=False to allow calls from asyncio loop callbacks
        return sqlite3.connect(self.path, check_same_thread=False)

    def _init(self):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    language TEXT DEFAULT 'ru',
                    role TEXT DEFAULT 'user'
                );
            """)
            conn.commit()

    # --- Users
    def upsert_user(
        self,
        user_id: int,
        username: Optional[str],
        language: Optional[str] = None,
        role: Optional[str] = None,
    ) -> bool:
        """Insert or update a user record.

        Returns ``True`` when a new record was created. This allows callers to
        adjust onboarding flows (e.g. send an extended welcome message on the
        first run).
        """
        normalized_language = (language or self.default_lang).lower()
        with self._connect() as conn:
            cur = conn.cursor()
            # Ensure existing first
            cur.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
            exists = cur.fetchone() is not None
            if not exists:
                cur.execute(
                    "INSERT INTO users(user_id, username, language, role) VALUES(?, ?, ?, ?)",
                    (user_id, username, normalized_language, role or "user"),
                )
            # Update fields conditionally
            if language is not None:
                cur.execute("UPDATE users SET language=? WHERE user_id=?", (normalized_language, user_id))
            if role is not None:
                cur.execute("UPDATE users SET role=? WHERE user_id=?", (role, user_id))
            if username is not None:
                cur.execute("UPDATE users SET username=? WHERE user_id=?", (username, user_id))
            conn.commit()
            return not exists

    def get_language(self, user_id: int) -> str:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT language FROM users WHERE user_id=?", (user_id,))
            row = cur.fetchone()
            return (row[0] if row and row[0] else self.default_lang).lower()

    def set_language(self, user_id: int, lang: str):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE users SET language=? WHERE user_id=?", (lang.lower(), user_id))
            conn.commit()

    def get_role(self, user_id: int) -> str:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT role FROM users WHERE user_id=?", (user_id,))
            row = cur.fetchone()
            return row[0] if row and row[0] else "user"

    def set_role(self, user_id: int, role: str):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE users SET role=? WHERE user_id=?", (role, user_id))
            conn.commit()
