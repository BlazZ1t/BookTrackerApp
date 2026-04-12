import sqlite3
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from src.backend.app import app
from src.backend.database.connection import get_database_connection, init_db


@pytest.fixture
def db_conn() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    init_db(conn)
    yield conn
    conn.close()


@pytest.fixture
def client(db_conn) -> Generator[TestClient, None, None]:
    def _override():
        try:
            yield db_conn
        finally:
            pass

    app.dependency_overrides[get_database_connection] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
