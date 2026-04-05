import sqlite3
from pathlib import Path

_MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def get_connection(db_path: str = "books.db") -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    for migration in sorted(_MIGRATIONS_DIR.glob("*.sql")):
        sql = migration.read_text(encoding="utf-8")
        conn.executescript(sql)
