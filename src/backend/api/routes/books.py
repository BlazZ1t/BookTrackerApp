import logging
import sqlite3
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from src.backend.api.dependencies import get_current_user_id
from src.backend.api.schemas.book import (
    BookListResponse,
    BookResponse,
    BookStatus,
    CreateBookRequest,
    UpdateBookRequest,
)
from src.backend.database.connection import get_database_connection
from src.backend.database.models.book import BookRecord
import src.backend.database.repository.books as books_repository

router = APIRouter(prefix="/books", tags=["books"])
logger = logging.getLogger(__name__)


def _derive_status(
    current_page: int,
    total_pages: Optional[int],
) -> Optional[str]:
    """
    Returns None when total_pages is not set (status cannot be derived)
    """
    if total_pages is None:
        return None
    if current_page == 0:
        return BookStatus.not_started.value
    if current_page >= total_pages:
        return BookStatus.completed.value
    return BookStatus.reading.value


def _to_response(book: BookRecord) -> BookResponse:
    return BookResponse(
        id=book.id,
        user_id=book.user_id,
        title=book.title,
        author=book.author,
        genre=book.genre,
        total_pages=book.total_pages,
        current_page=book.current_page,
        status=book.status,
        progress_percent=book.progress_percent(),
    )


@router.post("/", response_model=BookResponse, status_code=201)
async def create_book(
    body: CreateBookRequest,
    user_id: str = Depends(get_current_user_id),
    db: sqlite3.Connection = Depends(get_database_connection),
):
    status = (
        _derive_status(body.current_page, body.total_pages)
        or body.status.value
    )
    try:
        book = books_repository.create_book(
            db,
            user_id=user_id,
            title=body.title,
            author=body.author,
            status=status,
            genre=body.genre,
            total_pages=body.total_pages,
            current_page=body.current_page,
        )
    except Exception as e:
        logger.error("Failed to create book: %s", e)
        raise HTTPException(
            status_code=500,
            detail={"message": "Internal server error"},
        )
    return _to_response(book)


@router.get("/", response_model=BookListResponse)
async def get_books(
    title: Optional[str] = None,
    author: Optional[str] = None,
    genre: Optional[str] = None,
    status: Optional[BookStatus] = None,
    next_token: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    db: sqlite3.Connection = Depends(get_database_connection),
):
    try:
        books, token = books_repository.get_books(
            db,
            user_id=user_id,
            title=title,
            author=author,
            genre=genre,
            status=status.value if status else None,
            next_token=next_token,
            limit=limit,
        )
    except Exception as e:
        logger.error("Failed to fetch books: %s", e)
        raise HTTPException(
            status_code=500,
            detail={"message": "Internal server error"},
        )
    return BookListResponse(
        books=[_to_response(b) for b in books],
        next_token=token,
    )


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(
    book_id: str,
    user_id: str = Depends(get_current_user_id),
    db: sqlite3.Connection = Depends(get_database_connection),
):
    book = books_repository.get_book_by_id(db, book_id, user_id)
    if book is None:
        raise HTTPException(
            status_code=404,
            detail={"message": "Book not found"},
        )
    return _to_response(book)


@router.put("/{book_id}", response_model=BookResponse)
async def update_book(
    book_id: str,
    body: UpdateBookRequest,
    user_id: str = Depends(get_current_user_id),
    db: sqlite3.Connection = Depends(get_database_connection),
):
    existing = books_repository.get_book_by_id(db, book_id, user_id)
    if existing is None:
        raise HTTPException(
            status_code=404,
            detail={"message": "Book not found"},
        )

    effective_current = (
        body.current_page
        if body.current_page is not None
        else existing.current_page
    )
    effective_total = (
        body.total_pages
        if body.total_pages is not None
        else existing.total_pages
    )

    derived = _derive_status(effective_current, effective_total)
    status = derived or (body.status.value if body.status else None)

    try:
        book = books_repository.update_book(
            db,
            book_id=book_id,
            user_id=user_id,
            title=body.title,
            author=body.author,
            genre=body.genre,
            total_pages=body.total_pages,
            current_page=body.current_page,
            status=status,
        )
    except Exception as e:
        logger.error("Failed to update book: %s", e)
        raise HTTPException(
            status_code=500,
            detail={"message": "Internal server error"},
        )
    if book is None:
        raise HTTPException(
            status_code=404,
            detail={"message": "Book not found"},
        )
    return _to_response(book)


@router.delete("/{book_id}", status_code=204)
async def delete_book(
    book_id: str,
    user_id: str = Depends(get_current_user_id),
    db: sqlite3.Connection = Depends(get_database_connection),
):
    deleted = books_repository.delete_book(db, book_id, user_id)
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail={"message": "Book not found"},
        )
