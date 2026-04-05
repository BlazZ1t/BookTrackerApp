import pytest

from src.backend.database.repository.users import create_user
from src.backend.database.repository.books import (
    create_book,
    delete_book,
    get_book_by_id,
    get_books,
    update_book,
)
from src.backend.models.book import BookRecord


@pytest.fixture
def user(db_conn):
    return create_user(db_conn, username="alice", password_hash="hash")


@pytest.fixture
def other_user(db_conn):
    return create_user(db_conn, username="bob", password_hash="hash")


@pytest.fixture
def sample_book(db_conn, user):
    return create_book(
        db_conn,
        user_id=user.id,
        title="The Hobbit",
        author="Tolkien",
        status="not_started",
        genre="Fantasy",
        total_pages=310,
    )


# --- create_book ---

def test_create_book_returns_record(db_conn, user):
    book = create_book(
        db_conn,
        user_id=user.id,
        title="Dune",
        author="Herbert",
        status="not_started",
    )

    assert isinstance(book, BookRecord)
    assert book.id is not None
    assert book.user_id == user.id
    assert book.title == "Dune"
    assert book.author == "Herbert"
    assert book.current_page == 0
    assert book.genre is None
    assert book.total_pages is None


def test_create_book_with_all_fields(db_conn, user):
    book = create_book(
        db_conn,
        user_id=user.id,
        title="Dune",
        author="Herbert",
        status="reading",
        genre="Sci-Fi",
        total_pages=412,
        current_page=100,
    )

    assert book.genre == "Sci-Fi"
    assert book.total_pages == 412
    assert book.current_page == 100
    assert book.status == "reading"


# --- get_book_by_id ---

def test_get_book_by_id_found(db_conn, user, sample_book):
    found = get_book_by_id(db_conn, book_id=sample_book.id, user_id=user.id)

    assert found is not None
    assert found.id == sample_book.id
    assert found.title == "The Hobbit"


def test_get_book_by_id_not_found(db_conn, user):
    result = get_book_by_id(db_conn, book_id=999, user_id=user.id)

    assert result is None


def test_get_book_by_id_wrong_user_returns_none(db_conn, user, other_user, sample_book):
    result = get_book_by_id(db_conn, book_id=sample_book.id, user_id=other_user.id)

    assert result is None


# --- get_books ---

def test_get_books_returns_only_own_books(db_conn, user, other_user):
    create_book(db_conn, user_id=user.id, title="Book A", author="Author A", status="not_started")
    create_book(db_conn, user_id=other_user.id, title="Book B", author="Author B", status="not_started")

    books = get_books(db_conn, user_id=user.id)

    assert len(books) == 1
    assert books[0].title == "Book A"


def test_get_books_no_filter_returns_all(db_conn, user):
    create_book(db_conn, user_id=user.id, title="Book A", author="Author", status="not_started")
    create_book(db_conn, user_id=user.id, title="Book B", author="Author", status="reading")

    books = get_books(db_conn, user_id=user.id)

    assert len(books) == 2


def test_get_books_filter_by_title_partial(db_conn, user):
    create_book(db_conn, user_id=user.id, title="Harry Potter", author="Rowling", status="not_started")
    create_book(db_conn, user_id=user.id, title="The Hobbit", author="Tolkien", status="not_started")

    books = get_books(db_conn, user_id=user.id, title="harry")

    assert len(books) == 1
    assert books[0].title == "Harry Potter"


def test_get_books_filter_by_author_partial(db_conn, user):
    create_book(db_conn, user_id=user.id, title="Harry Potter", author="J.K. Rowling", status="not_started")
    create_book(db_conn, user_id=user.id, title="The Hobbit", author="Tolkien", status="not_started")

    books = get_books(db_conn, user_id=user.id, author="rowling")

    assert len(books) == 1
    assert books[0].author == "J.K. Rowling"


def test_get_books_filter_by_genre_exact(db_conn, user):
    create_book(db_conn, user_id=user.id, title="Dune", author="Herbert", status="not_started", genre="Sci-Fi")
    create_book(db_conn, user_id=user.id, title="The Hobbit", author="Tolkien", status="not_started", genre="Fantasy")

    books = get_books(db_conn, user_id=user.id, genre="fantasy")

    assert len(books) == 1
    assert books[0].title == "The Hobbit"


def test_get_books_filter_by_status_exact(db_conn, user):
    create_book(db_conn, user_id=user.id, title="Book A", author="Author", status="reading")
    create_book(db_conn, user_id=user.id, title="Book B", author="Author", status="completed")

    books = get_books(db_conn, user_id=user.id, status="reading")

    assert len(books) == 1
    assert books[0].title == "Book A"


def test_get_books_filter_case_insensitive(db_conn, user):
    create_book(db_conn, user_id=user.id, title="HARRY POTTER", author="ROWLING", status="not_started", genre="FANTASY")

    assert len(get_books(db_conn, user_id=user.id, title="harry")) == 1
    assert len(get_books(db_conn, user_id=user.id, author="rowling")) == 1
    assert len(get_books(db_conn, user_id=user.id, genre="fantasy")) == 1


def test_get_books_combined_filters(db_conn, user):
    create_book(db_conn, user_id=user.id, title="Dune", author="Herbert", status="reading", genre="Sci-Fi")
    create_book(db_conn, user_id=user.id, title="Foundation", author="Asimov", status="reading", genre="Sci-Fi")
    create_book(db_conn, user_id=user.id, title="The Hobbit", author="Tolkien", status="reading", genre="Fantasy")

    books = get_books(db_conn, user_id=user.id, genre="Sci-Fi", status="reading")

    assert len(books) == 2


def test_get_books_no_match_returns_empty(db_conn, user):
    create_book(db_conn, user_id=user.id, title="Dune", author="Herbert", status="not_started")

    books = get_books(db_conn, user_id=user.id, title="nonexistent")

    assert books == []


# --- update_book ---

def test_update_book_single_field(db_conn, user, sample_book):
    updated = update_book(db_conn, book_id=sample_book.id, user_id=user.id, status="reading")

    assert updated is not None
    assert updated.status == "reading"
    assert updated.title == sample_book.title


def test_update_book_multiple_fields(db_conn, user, sample_book):
    updated = update_book(
        db_conn,
        book_id=sample_book.id,
        user_id=user.id,
        current_page=150,
        status="reading",
    )

    assert updated.current_page == 150
    assert updated.status == "reading"


def test_update_book_no_fields_returns_unchanged(db_conn, user, sample_book):
    updated = update_book(db_conn, book_id=sample_book.id, user_id=user.id)

    assert updated is not None
    assert updated.title == sample_book.title
    assert updated.status == sample_book.status


def test_update_book_wrong_user_returns_none(db_conn, user, other_user, sample_book):
    result = update_book(
        db_conn,
        book_id=sample_book.id,
        user_id=other_user.id,
        status="reading",
    )

    assert result is None


def test_update_book_not_found_returns_none(db_conn, user):
    result = update_book(db_conn, book_id=999, user_id=user.id, status="reading")

    assert result is None


# --- delete_book ---

def test_delete_book_returns_true(db_conn, user, sample_book):
    result = delete_book(db_conn, book_id=sample_book.id, user_id=user.id)

    assert result is True


def test_delete_book_removes_from_db(db_conn, user, sample_book):
    delete_book(db_conn, book_id=sample_book.id, user_id=user.id)

    found = get_book_by_id(db_conn, book_id=sample_book.id, user_id=user.id)
    assert found is None


def test_delete_book_wrong_user_returns_false(db_conn, user, other_user, sample_book):
    result = delete_book(db_conn, book_id=sample_book.id, user_id=other_user.id)

    assert result is False


def test_delete_book_wrong_user_does_not_remove(db_conn, user, other_user, sample_book):
    delete_book(db_conn, book_id=sample_book.id, user_id=other_user.id)

    found = get_book_by_id(db_conn, book_id=sample_book.id, user_id=user.id)
    assert found is not None


def test_delete_book_not_found_returns_false(db_conn, user):
    result = delete_book(db_conn, book_id=999, user_id=user.id)

    assert result is False
