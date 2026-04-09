import sqlite3
from pathlib import Path
from typing import Iterator

_MIGRATIONS_DIR = Path(__file__).parent / "migrations"

def get_connection(db_path: str = "books.db") -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def get_database_connection() -> Iterator[sqlite3.Connection]:
    """
    This function is an abstraction of get_connection() that closes
    automatically and doesn't require a string for the db_path, which can be adjusted
    Usage:
    from src.backend.database.connection import get_database_connection
    async def login(database: sqlite3.Connection = Depends(get_database_connection)):
    """
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


def init_db(conn: sqlite3.Connection) -> None:
    for migration in sorted(_MIGRATIONS_DIR.glob("*.sql")):
        sql = migration.read_text(encoding="utf-8")
        conn.executescript(sql)
