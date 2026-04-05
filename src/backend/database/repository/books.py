import sqlite3
from typing import Optional

from src.backend.models.book import BookRecord


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
        "SELECT id, user_id, title, author, genre, total_pages,"
        " current_page, status FROM books WHERE id = ? AND user_id = ?",
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
    rows = conn.execute(
        "SELECT id, user_id, title, author, genre, total_pages,"
        " current_page, status FROM books"
        " WHERE user_id = ?"
        " AND (? IS NULL OR LOWER(title) LIKE '%' || LOWER(?) || '%')"
        " AND (? IS NULL OR LOWER(author) LIKE '%' || LOWER(?) || '%')"
        " AND (? IS NULL OR LOWER(genre) = LOWER(?))"
        " AND (? IS NULL OR status = ?)",
        (user_id, title, title, author, author, genre, genre, status, status),
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
    conn.execute(
        """
        UPDATE books SET
            title        = COALESCE(?, title),
            author       = COALESCE(?, author),
            genre        = COALESCE(?, genre),
            total_pages  = COALESCE(?, total_pages),
            current_page = COALESCE(?, current_page),
            status       = COALESCE(?, status)
        WHERE id = ? AND user_id = ?
        """,
        (title, author, genre, total_pages, current_page, status,
         book_id, user_id),
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
