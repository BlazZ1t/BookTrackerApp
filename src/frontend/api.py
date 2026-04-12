import json
import urllib.parse
import urllib.request
import urllib.error
from typing import Any, Optional

from constants import API_BASE_URL


class APIError(Exception):
    pass


def _make_headers(token: Optional[str] = None) -> dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _request(
    method: str,
    path: str,
    token: Optional[str] = None,
    data: Optional[dict[str, Any]] = None,
    params: Optional[dict[str, Any]] = None,
) -> Any:
    
    url = f"{API_BASE_URL}{path}"
    if params:
        clean_params = {
            key: value
            for key, value in params.items()
            if value not in (None, "", [])
        }
        if clean_params:
            url += "?" + urllib.parse.urlencode(clean_params)

    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")

    req = urllib.request.Request(
        url=url,
        data=body,
        headers=_make_headers(token),
        method=method,
    )

    try:
        with urllib.request.urlopen(req) as response:
            raw = response.read().decode("utf-8").strip()
            if not raw:
                return None

            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return {"raw_response": raw}

    except urllib.error.HTTPError as exc:
        error_text = exc.read().decode("utf-8", errors="ignore")
        try:
            error_json = json.loads(error_text)
            detail = error_json.get("detail", error_text)
        except json.JSONDecodeError:
            detail = error_text or f"HTTP {exc.code}"
        raise APIError(str(detail)) from exc

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