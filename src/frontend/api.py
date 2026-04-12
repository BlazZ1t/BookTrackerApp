import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from constants import API_BASE_URL


class APIError(Exception):
    pass


def _make_headers(token: str | None = None) -> dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _build_url(path: str, params: dict[str, Any] | None = None) -> str:
    url = f"{API_BASE_URL}{path}"
    if not params:
        return url

    clean_params = {
        key: value
        for key, value in params.items()
        if value not in (None, "", [])
    }
    if clean_params:
        url += "?" + urllib.parse.urlencode(clean_params)
    return url


def _encode_body(data: dict[str, Any] | None = None) -> bytes | None:
    if data is None:
        return None
    return json.dumps(data).encode("utf-8")


def _parse_response_body(raw: str) -> Any:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw_response": raw}


def _extract_error_detail(exc: urllib.error.HTTPError) -> str:
    error_text = exc.read().decode("utf-8", errors="ignore")
    try:
        error_json = json.loads(error_text)
        return str(error_json.get("detail", error_text))
    except json.JSONDecodeError:
        return error_text or f"HTTP {exc.code}"


def _request(
    method: str,
    path: str,
    token: str | None = None,
    data: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> Any:
    req = urllib.request.Request(
        url=_build_url(path, params),
        data=_encode_body(data),
        headers=_make_headers(token),
        method=method,
    )

    try:
        with urllib.request.urlopen(req) as response:  # nosec B310
            raw = response.read().decode("utf-8").strip()
            return _parse_response_body(raw)
    except urllib.error.HTTPError as exc:
        raise APIError(_extract_error_detail(exc)) from exc
    except urllib.error.URLError as exc:
        raise APIError(f"Couldn't connect to API: {exc.reason}") from exc


def register(username: str, password: str) -> Any:
    return _request(
        method="POST",
        path="/auth/register",
        data={
            "login": username,
            "password": password,
        },
    )


def login(username: str, password: str) -> str:
    response = _request(
        method="POST",
        path="/auth/login",
        data={
            "login": username,
            "password": password,
        },
    )

    token = response.get("jwt_token")
    if not token:
        raise APIError("Server didn't return jwt_token")
    return token


def get_books(
    token: str,
    title: str = "",
    author: str = "",
    genre: str = "",
    status: str = "",
) -> list[dict[str, Any]]:
    response = _request(
        method="GET",
        path="/books/",
        token=token,
        params={
            "title": title,
            "author": author,
            "genre": genre,
            "status": status,
        },
    )

    if isinstance(response, list):
        return response

    if isinstance(response, dict):
        if "books" in response:
            return response["books"]
        if "items" in response:
            return response["items"]

    return []


def create_book(token: str, payload: dict[str, Any]) -> Any:
    return _request(
        method="POST",
        path="/books/",
        token=token,
        data=payload,
    )


def update_book(token: str, book_id: str, payload: dict[str, Any]) -> Any:
    return _request(
        method="PUT",
        path=f"/books/{book_id}",
        token=token,
        data=payload,
    )


def delete_book(token: str, book_id: str) -> Any:
    return _request(
        method="DELETE",
        path=f"/books/{book_id}",
        token=token,
    )


def get_book(token: str, book_id: str) -> Any:
    return _request(
        method="GET",
        path=f"/books/{book_id}",
        token=token,
    )
