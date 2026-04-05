import sqlite3
from collections.abc import Generator

import pytest

from src.backend.database.connection import init_db


@pytest.fixture
def db_conn() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    init_db(conn)
    yield conn
    conn.close()
