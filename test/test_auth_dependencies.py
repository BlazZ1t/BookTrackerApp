from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt

from src.backend.api.dependencies import get_current_user_id
from src.backend.api.routes.auth import ALGORITHM, SECRET_KEY, create_jwt_token


def _credentials(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def test_get_current_user_id_returns_sub_from_valid_token():
    token = create_jwt_token({"sub": "user-123"})

    assert get_current_user_id(_credentials(token)) == "user-123"


def test_get_current_user_id_rejects_token_without_sub():
    token = create_jwt_token({"scope": "books"})

    with pytest.raises(HTTPException) as exc_info:
        get_current_user_id(_credentials(token))

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == {"message": "Invalid token: missing subject"}


def test_get_current_user_id_rejects_invalid_token():
    with pytest.raises(HTTPException) as exc_info:
        get_current_user_id(_credentials("not-a-jwt"))

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == {"message": "Invalid or expired token"}


def test_get_current_user_id_rejects_expired_token():
    token = jwt.encode(
        {
            "sub": "user-123",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    with pytest.raises(HTTPException) as exc_info:
        get_current_user_id(_credentials(token))

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == {"message": "Invalid or expired token"}
