import sqlite3
import pytest

from src.backend.database.repository.users import (
    create_user,
    get_user_by_id,
    get_user_by_username,
)
from src.backend.database.models.user import UserRecord


def test_create_user_returns_record(db_conn):
    user = create_user(db_conn, username="alice", password_hash="hashed_pw")

    assert isinstance(user, UserRecord)
    assert user.id is not None
    assert user.username == "alice"
    assert user.password_hash == "hashed_pw"


def test_create_user_assigns_unique_ids(db_conn):
    user1 = create_user(db_conn, username="alice", password_hash="hash1")
    user2 = create_user(db_conn, username="bob", password_hash="hash2")

    assert user1.id != user2.id


def test_create_user_duplicate_username_raises(db_conn):
    create_user(db_conn, username="alice", password_hash="hash1")

    with pytest.raises(sqlite3.IntegrityError):
        create_user(db_conn, username="alice", password_hash="hash2")


def test_get_user_by_username_found(db_conn):
    created = create_user(db_conn, username="alice", password_hash="hashed_pw")

    found = get_user_by_username(db_conn, "alice")

    assert found is not None
    assert found.id == created.id
    assert found.username == "alice"
    assert found.password_hash == "hashed_pw"


def test_get_user_by_username_not_found(db_conn):
    result = get_user_by_username(db_conn, "nonexistent")

    assert result is None


def test_get_user_by_id_found(db_conn):
    created = create_user(db_conn, username="alice", password_hash="hashed_pw")

    found = get_user_by_id(db_conn, created.id)

    assert found is not None
    assert found.id == created.id
    assert found.username == "alice"


def test_create_user_id_is_uuid_string(db_conn):
    user = create_user(db_conn, username="alice", password_hash="hash")

    assert isinstance(user.id, str)
    assert len(user.id) == 36


def test_get_user_by_id_not_found(db_conn):
    result = get_user_by_id(db_conn, user_id="nonexistent-id")

    assert result is None
