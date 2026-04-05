import logging
import sqlite3
from uuid import uuid4
from typing import Optional

from src.backend.database.models.user import UserRecord

logger = logging.getLogger(__name__)


def create_user(
    conn: sqlite3.Connection,
    username: str,
    password_hash: str,
) -> UserRecord:
    logger.debug("Creating user: username=%s", username)
    user_id = str(uuid4())
    conn.execute(
        "INSERT INTO users (id, username, password_hash) VALUES (?, ?, ?)",
        (user_id, username, password_hash),
    )
    conn.commit()
    user = UserRecord(
        id=user_id, username=username, password_hash=password_hash
    )
    logger.debug("User created: id=%s, username=%s", user.id, user.username)
    return user


def get_user_by_username(
    conn: sqlite3.Connection,
    username: str,
) -> Optional[UserRecord]:
    logger.debug("Fetching user by username: %s", username)
    row = conn.execute(
        "SELECT id, username, password_hash FROM users WHERE username = ?",
        (username,),
    ).fetchone()
    if row is None:
        logger.debug("User not found: username=%s", username)
        return None
    return UserRecord(
        id=row["id"],
        username=row["username"],
        password_hash=row["password_hash"],
    )


def get_user_by_id(
    conn: sqlite3.Connection,
    user_id: str,
) -> Optional[UserRecord]:
    logger.debug("Fetching user by id: %s", user_id)
    row = conn.execute(
        "SELECT id, username, password_hash FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    if row is None:
        logger.debug("User not found: id=%s", user_id)
        return None
    return UserRecord(
        id=row["id"],
        username=row["username"],
        password_hash=row["password_hash"],
    )
