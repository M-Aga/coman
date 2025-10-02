import os, sqlite3
from coman.core.config import settings
DB_PATH = os.path.join(settings.data_dir, "logic.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn
def init_db():
    conn = get_conn()
    conn.execute("""CREATE TABLE IF NOT EXISTS facts(id INTEGER PRIMARY KEY AUTOINCREMENT,label TEXT UNIQUE,value TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS rules(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,if_label TEXT,if_value TEXT,then_label TEXT,then_value TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS rules_ext(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,expr_json TEXT,action_json TEXT,priority INTEGER DEFAULT 0,enabled INTEGER DEFAULT 1)""")
    conn.commit(); conn.close()
init_db()
