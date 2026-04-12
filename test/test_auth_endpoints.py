from fastapi import HTTPException

import src.backend.api.routes.auth as auth_route


def test_register_returns_created(client):
    response = client.post(
        "/auth/register",
        json={"login": "alice", "password": "pass"},
    )

    assert response.status_code == 201
    assert response.json() == {"message": "User registered"}


def test_register_duplicate_username_returns_conflict(client):
    client.post(
        "/auth/register",
        json={"login": "alice", "password": "pass"},
    )

    response = client.post(
        "/auth/register",
        json={"login": "alice", "password": "pass"},
    )

    assert response.status_code == 409
    assert response.json() == {"detail": {"message": "Username already taken"}}


def test_login_returns_jwt_token(client):
    client.post(
        "/auth/register",
        json={"login": "alice", "password": "pass"},
    )

    response = client.post(
        "/auth/login",
        json={"login": "alice", "password": "pass"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["jwt_token"], str)
    assert body["jwt_token"]


def test_login_unknown_user_returns_unauthorized(client):
    response = client.post(
        "/auth/login",
        json={"login": "alice", "password": "pass"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": {"message": "Invalid credentials"}}


def test_login_wrong_password_returns_unauthorized(client):
    client.post(
        "/auth/register",
        json={"login": "alice", "password": "pass"},
    )

    response = client.post(
        "/auth/login",
        json={"login": "alice", "password": "wrong"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": {"message": "Invalid credentials"}}


def test_register_reraises_http_exception(client, monkeypatch):
    def raise_http_exception(*args, **kwargs):
        raise HTTPException(status_code=418, detail={"message": "teapot"})

    monkeypatch.setattr(
        auth_route.users_repository,
        "create_user",
        raise_http_exception,
    )

    response = client.post(
        "/auth/register",
        json={"login": "alice", "password": "pass"},
    )

    assert response.status_code == 418
    assert response.json() == {"detail": {"message": "teapot"}}


def test_register_unexpected_error_returns_internal_server_error(client, monkeypatch):
    def raise_unexpected_error(*args, **kwargs):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(
        auth_route.users_repository,
        "create_user",
        raise_unexpected_error,
    )

    response = client.post(
        "/auth/register",
        json={"login": "alice", "password": "pass"},
    )

    assert response.status_code == 500
    assert response.json() == {"detail": {"message": "Internal server error"}}


def test_login_unexpected_error_returns_internal_server_error(client, monkeypatch):
    def raise_unexpected_error(*args, **kwargs):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(
        auth_route.users_repository,
        "get_user_by_username",
        raise_unexpected_error,
    )

    response = client.post(
        "/auth/login",
        json={"login": "alice", "password": "pass"},
    )

    assert response.status_code == 500
    assert response.json() == {"detail": {"message": "Internal server error"}}


def test_hash_password_can_be_verified():
    password_hash = auth_route.hash_password("pass")

    assert auth_route.verify_password("pass", password_hash) is True
    assert auth_route.verify_password("wrong", password_hash) is False
