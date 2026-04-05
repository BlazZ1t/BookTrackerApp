import sqlite3
from typing import Optional

from src.backend.models.user import UserRecord


def create_user(
    conn: sqlite3.Connection,
    username: str,
    password_hash: str,
) -> UserRecord:
    cursor = conn.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        (username, password_hash),
    )
    conn.commit()
    return UserRecord(
        id=cursor.lastrowid,
        username=username,
        password_hash=password_hash,
    )


def get_user_by_username(
    conn: sqlite3.Connection,
    username: str,
) -> Optional[UserRecord]:
    row = conn.execute(
        "SELECT id, username, password_hash FROM users WHERE username = ?",
        (username,),
    ).fetchone()
    if row is None:
        return None
    return UserRecord(
        id=row["id"],
        username=row["username"],
        password_hash=row["password_hash"],
    )


def get_user_by_id(
    conn: sqlite3.Connection,
    user_id: int,
) -> Optional[UserRecord]:
    row = conn.execute(
        "SELECT id, username, password_hash FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    if row is None:
        return None
    return UserRecord(
        id=row["id"],
        username=row["username"],
        password_hash=row["password_hash"],
    )
