import io
import sys
import urllib.error
from pathlib import Path

import pytest


FRONTEND_DIR = Path(__file__).resolve().parents[1] / "src" / "frontend"
if str(FRONTEND_DIR) not in sys.path:
    sys.path.insert(0, str(FRONTEND_DIR))

import api as frontend_api  # noqa: E402


class FakeResponse:
    def __init__(self, body: str):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return self.body.encode("utf-8")


def test_make_headers_without_token():
    assert frontend_api._make_headers() == {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def test_make_headers_with_token():
    assert frontend_api._make_headers("token")["Authorization"] == "Bearer token"


def test_request_sends_json_body_headers_and_clean_query_params(monkeypatch):
    captured = {}

    def fake_urlopen(request):
        captured["url"] = request.full_url
        captured["method"] = request.get_method()
        captured["data"] = request.data
        captured["content_type"] = request.get_header("Content-type")
        captured["authorization"] = request.get_header("Authorization")
        return FakeResponse('{"ok": true}')

    monkeypatch.setattr(frontend_api.urllib.request, "urlopen", fake_urlopen)

    response = frontend_api._request(
        method="POST",
        path="/books/",
        token="jwt",
        data={"title": "Dune"},
        params={
            "title": "Dune",
            "author": "",
            "genre": None,
            "status": [],
        },
    )

    assert response == {"ok": True}
    assert captured["url"] == "http://localhost:8000/books/?title=Dune"
    assert captured["method"] == "POST"
    assert captured["data"] == b'{"title": "Dune"}'
    assert captured["content_type"] == "application/json"
    assert captured["authorization"] == "Bearer jwt"


def test_request_returns_none_for_empty_response(monkeypatch):
    monkeypatch.setattr(
        frontend_api.urllib.request,
        "urlopen",
        lambda request: FakeResponse("   "),
    )

    assert frontend_api._request("DELETE", "/books/book-id") is None


def test_request_wraps_non_json_response(monkeypatch):
    monkeypatch.setattr(
        frontend_api.urllib.request,
        "urlopen",
        lambda request: FakeResponse("deleted"),
    )

    assert frontend_api._request("GET", "/health") == {"raw_response": "deleted"}


def test_request_raises_api_error_from_http_error_json_detail(monkeypatch):
    def fake_urlopen(request):
        raise urllib.error.HTTPError(
            url=request.full_url,
            code=409,
            msg="Conflict",
            hdrs=None,
            fp=io.BytesIO(b'{"detail": {"message": "Username already taken"}}'),
        )

    monkeypatch.setattr(frontend_api.urllib.request, "urlopen", fake_urlopen)

    with pytest.raises(frontend_api.APIError) as exc_info:
        frontend_api._request("POST", "/auth/register")

    assert str(exc_info.value) == "{'message': 'Username already taken'}"


def test_request_raises_api_error_from_http_error_text(monkeypatch):
    def fake_urlopen(request):
        raise urllib.error.HTTPError(
            url=request.full_url,
            code=500,
            msg="Server Error",
            hdrs=None,
            fp=io.BytesIO(b"boom"),
        )

    monkeypatch.setattr(frontend_api.urllib.request, "urlopen", fake_urlopen)

    with pytest.raises(frontend_api.APIError) as exc_info:
        frontend_api._request("GET", "/books/")

    assert str(exc_info.value) == "boom"


def test_request_raises_api_error_from_url_error(monkeypatch):
    def fake_urlopen(request):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(frontend_api.urllib.request, "urlopen", fake_urlopen)

    with pytest.raises(frontend_api.APIError) as exc_info:
        frontend_api._request("GET", "/books/")

    assert str(exc_info.value) == "Couldn't connect to API: connection refused"


def test_register_delegates_to_request(monkeypatch):
    calls = []
    monkeypatch.setattr(frontend_api, "_request", lambda **kwargs: calls.append(kwargs) or {"ok": True})

    assert frontend_api.register("alice", "pass") == {"ok": True}
    assert calls == [
        {
            "method": "POST",
            "path": "/auth/register",
            "data": {"login": "alice", "password": "pass"},
        }
    ]


def test_login_returns_jwt_token(monkeypatch):
    monkeypatch.setattr(
        frontend_api,
        "_request",
        lambda **kwargs: {"jwt_token": "jwt"},
    )

    assert frontend_api.login("alice", "pass") == "jwt"


def test_login_raises_when_token_is_missing(monkeypatch):
    monkeypatch.setattr(frontend_api, "_request", lambda **kwargs: {})

    with pytest.raises(frontend_api.APIError) as exc_info:
        frontend_api.login("alice", "pass")

    assert str(exc_info.value) == "Server didn't return jwt_token"


def test_get_books_accepts_books_items_list_and_unknown_shapes(monkeypatch):
    responses = iter(
        [
            [{"id": "1"}],
            {"books": [{"id": "2"}]},
            {"items": [{"id": "3"}]},
            {"unexpected": []},
        ]
    )
    monkeypatch.setattr(frontend_api, "_request", lambda **kwargs: next(responses))

    assert frontend_api.get_books("jwt") == [{"id": "1"}]
    assert frontend_api.get_books("jwt") == [{"id": "2"}]
    assert frontend_api.get_books("jwt") == [{"id": "3"}]
    assert frontend_api.get_books("jwt") == []


def test_book_actions_delegate_to_request(monkeypatch):
    calls = []
    monkeypatch.setattr(frontend_api, "_request", lambda **kwargs: calls.append(kwargs) or {"ok": True})

    assert frontend_api.create_book("jwt", {"title": "Dune"}) == {"ok": True}
    assert frontend_api.update_book("jwt", "book-id", {"title": "Dune"}) == {"ok": True}
    assert frontend_api.delete_book("jwt", "book-id") == {"ok": True}
    assert frontend_api.get_book("jwt", "book-id") == {"ok": True}
    assert calls == [
        {
            "method": "POST",
            "path": "/books/",
            "token": "jwt",
            "data": {"title": "Dune"},
        },
        {
            "method": "PUT",
            "path": "/books/book-id",
            "token": "jwt",
            "data": {"title": "Dune"},
        },
        {
            "method": "DELETE",
            "path": "/books/book-id",
            "token": "jwt",
        },
        {
            "method": "GET",
            "path": "/books/book-id",
            "token": "jwt",
        },
    ]
