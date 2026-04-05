import sqlite3
from typing import Optional

from src.backend.models.book import BookRecord

_SELECT_COLUMNS = (
    "id, user_id, title, author, genre, total_pages, current_page, status"
)


def _row_to_book(row: sqlite3.Row) -> BookRecord:
    return BookRecord(
        id=row["id"],
        user_id=row["user_id"],
        title=row["title"],
        author=row["author"],
        genre=row["genre"],
        total_pages=row["total_pages"],
        current_page=row["current_page"],
        status=row["status"],
    )


def create_book(
    conn: sqlite3.Connection,
    user_id: int,
    title: str,
    author: str,
    status: str,
    genre: Optional[str] = None,
    total_pages: Optional[int] = None,
    current_page: int = 0,
) -> BookRecord:
    cursor = conn.execute(
        """
        INSERT INTO books
            (user_id, title, author, genre, total_pages, current_page, status)
        VALUES
            (?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, title, author, genre, total_pages, current_page, status),
    )
    conn.commit()
    return BookRecord(
        id=cursor.lastrowid,
        user_id=user_id,
        title=title,
        author=author,
        genre=genre,
        total_pages=total_pages,
        current_page=current_page,
        status=status,
    )


def get_book_by_id(
    conn: sqlite3.Connection,
    book_id: int,
    user_id: int,
) -> Optional[BookRecord]:
    row = conn.execute(
        f"SELECT {_SELECT_COLUMNS} FROM books WHERE id = ? AND user_id = ?",
        (book_id, user_id),
    ).fetchone()
    return _row_to_book(row) if row else None


def get_books(
    conn: sqlite3.Connection,
    user_id: int,
    *,
    title: Optional[str] = None,
    author: Optional[str] = None,
    genre: Optional[str] = None,
    status: Optional[str] = None,
) -> list[BookRecord]:
    conditions = ["user_id = ?"]
    params: list = [user_id]

    if title is not None:
        conditions.append("LOWER(title) LIKE '%' || LOWER(?) || '%'")
        params.append(title)
    if author is not None:
        conditions.append("LOWER(author) LIKE '%' || LOWER(?) || '%'")
        params.append(author)
    if genre is not None:
        conditions.append("LOWER(genre) = LOWER(?)")
        params.append(genre)
    if status is not None:
        conditions.append("status = ?")
        params.append(status)

    where = " AND ".join(conditions)
    rows = conn.execute(
        f"SELECT {_SELECT_COLUMNS} FROM books WHERE {where}",
        params,
    ).fetchall()
    return [_row_to_book(row) for row in rows]


def update_book(
    conn: sqlite3.Connection,
    book_id: int,
    user_id: int,
    *,
    title: Optional[str] = None,
    author: Optional[str] = None,
    genre: Optional[str] = None,
    total_pages: Optional[int] = None,
    current_page: Optional[int] = None,
    status: Optional[str] = None,
) -> Optional[BookRecord]:
    fields = {
        "title": title,
        "author": author,
        "genre": genre,
        "total_pages": total_pages,
        "current_page": current_page,
        "status": status,
    }
    updates = {k: v for k, v in fields.items() if v is not None}
    if not updates:
        return get_book_by_id(conn, book_id, user_id)

    set_clause = ", ".join(f"{col} = ?" for col in updates)
    params = list(updates.values()) + [book_id, user_id]

    conn.execute(
        f"UPDATE books SET {set_clause} WHERE id = ? AND user_id = ?",
        params,
    )
    conn.commit()
    return get_book_by_id(conn, book_id, user_id)


def delete_book(
    conn: sqlite3.Connection,
    book_id: int,
    user_id: int,
) -> bool:
    cursor = conn.execute(
        "DELETE FROM books WHERE id = ? AND user_id = ?",
        (book_id, user_id),
    )
    conn.commit()
    return cursor.rowcount > 0
