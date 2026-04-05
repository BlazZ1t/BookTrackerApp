import logging
import sqlite3
from typing import Optional

from src.backend.database.models.book import BookRecord

logger = logging.getLogger(__name__)


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
    logger.debug(
        "Creating book: user_id=%d, title=%r, author=%r",
        user_id, title, author,
    )
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
    book = BookRecord(
        id=cursor.lastrowid,
        user_id=user_id,
        title=title,
        author=author,
        genre=genre,
        total_pages=total_pages,
        current_page=current_page,
        status=status,
    )
    logger.debug("Book created: id=%d, user_id=%d", book.id, book.user_id)
    return book


def get_book_by_id(
    conn: sqlite3.Connection,
    book_id: int,
    user_id: int,
) -> Optional[BookRecord]:
    logger.debug(
        "Fetching book: book_id=%d, user_id=%d", book_id, user_id
    )
    row = conn.execute(
        "SELECT id, user_id, title, author, genre, total_pages,"
        " current_page, status FROM books WHERE id = ? AND user_id = ?",
        (book_id, user_id),
    ).fetchone()
    if row is None:
        logger.debug(
            "Book not found: book_id=%d, user_id=%d", book_id, user_id
        )
        return None
    return _row_to_book(row)


def get_books(
    conn: sqlite3.Connection,
    user_id: int,
    *,
    title: Optional[str] = None,
    author: Optional[str] = None,
    genre: Optional[str] = None,
    status: Optional[str] = None,
    next_token: Optional[int] = None,
    limit: int = 20,
) -> tuple[list[BookRecord], Optional[int]]:
    logger.debug(
        "Fetching books: user_id=%d, title=%r, author=%r,"
        " genre=%r, status=%r, next_token=%r, limit=%d",
        user_id, title, author, genre, status, next_token, limit,
    )
    rows = conn.execute(
        "SELECT id, user_id, title, author, genre, total_pages,"
        " current_page, status FROM books"
        " WHERE user_id = ?"
        " AND (? IS NULL OR LOWER(title) LIKE '%' || LOWER(?) || '%')"
        " AND (? IS NULL OR LOWER(author) LIKE '%' || LOWER(?) || '%')"
        " AND (? IS NULL OR LOWER(genre) = LOWER(?))"
        " AND (? IS NULL OR status = ?)"
        " AND (? IS NULL OR id > ?)"
        " ORDER BY id ASC"
        " LIMIT ?",
        (user_id, title, title, author, author, genre, genre,
         status, status, next_token, next_token, limit + 1),
    ).fetchall()
    books = [_row_to_book(row) for row in rows[:limit]]
    next_token_out = books[-1].id if len(rows) > limit else None
    logger.debug(
        "Books fetched: user_id=%d, count=%d, next_token=%r",
        user_id, len(books), next_token_out,
    )
    return books, next_token_out


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
    logger.debug(
        "Updating book: book_id=%d, user_id=%d", book_id, user_id
    )
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
    book = get_book_by_id(conn, book_id, user_id)
    if book is None:
        logger.debug(
            "Update had no effect: book_id=%d, user_id=%d", book_id, user_id
        )
    return book


def delete_book(
    conn: sqlite3.Connection,
    book_id: int,
    user_id: int,
) -> bool:
    logger.debug(
        "Deleting book: book_id=%d, user_id=%d", book_id, user_id
    )
    cursor = conn.execute(
        "DELETE FROM books WHERE id = ? AND user_id = ?",
        (book_id, user_id),
    )
    conn.commit()
    deleted = cursor.rowcount > 0
    logger.debug(
        "Book deletion result: book_id=%d, deleted=%s", book_id, deleted
    )
    return deleted
