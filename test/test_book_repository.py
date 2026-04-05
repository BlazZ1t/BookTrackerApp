import pytest

from src.backend.database.repository.users import create_user
from src.backend.database.repository.books import (
    create_book,
    delete_book,
    get_book_by_id,
    get_books,
    update_book,
)
from src.backend.database.models.book import BookRecord


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
    assert isinstance(book.id, str)
    assert len(book.id) == 36
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


def test_get_book_by_id_wrong_user_returns_none(
    db_conn, user, other_user, sample_book
):
    result = get_book_by_id(
        db_conn, book_id=sample_book.id, user_id=other_user.id
    )

    assert result is None


# --- get_books ---

def test_get_books_returns_only_own_books(db_conn, user, other_user):
    create_book(
        db_conn,
        user_id=user.id,
        title="Book A",
        author="Author A",
        status="not_started",
    )
    create_book(
        db_conn,
        user_id=other_user.id,
        title="Book B",
        author="Author B",
        status="not_started",
    )

    books, _ = get_books(db_conn, user_id=user.id)

    assert len(books) == 1
    assert books[0].title == "Book A"


def test_get_books_no_filter_returns_all(db_conn, user):
    create_book(
        db_conn,
        user_id=user.id,
        title="Book A",
        author="Author",
        status="not_started",
    )
    create_book(
        db_conn,
        user_id=user.id,
        title="Book B",
        author="Author",
        status="reading",
    )

    books, _ = get_books(db_conn, user_id=user.id)

    assert len(books) == 2


def test_get_books_filter_by_title_partial(db_conn, user):
    create_book(
        db_conn,
        user_id=user.id,
        title="Harry Potter",
        author="Rowling",
        status="not_started",
    )
    create_book(
        db_conn,
        user_id=user.id,
        title="The Hobbit",
        author="Tolkien",
        status="not_started",
    )

    books, _ = get_books(db_conn, user_id=user.id, title="harry")

    assert len(books) == 1
    assert books[0].title == "Harry Potter"


def test_get_books_filter_by_author_partial(db_conn, user):
    create_book(
        db_conn,
        user_id=user.id,
        title="Harry Potter",
        author="J.K. Rowling",
        status="not_started",
    )
    create_book(
        db_conn,
        user_id=user.id,
        title="The Hobbit",
        author="Tolkien",
        status="not_started",
    )

    books, _ = get_books(db_conn, user_id=user.id, author="rowling")

    assert len(books) == 1
    assert books[0].author == "J.K. Rowling"


def test_get_books_filter_by_genre_exact(db_conn, user):
    create_book(
        db_conn,
        user_id=user.id,
        title="Dune",
        author="Herbert",
        status="not_started",
        genre="Sci-Fi",
    )
    create_book(
        db_conn,
        user_id=user.id,
        title="The Hobbit",
        author="Tolkien",
        status="not_started",
        genre="Fantasy",
    )

    books, _ = get_books(db_conn, user_id=user.id, genre="fantasy")

    assert len(books) == 1
    assert books[0].title == "The Hobbit"


def test_get_books_filter_by_status_exact(db_conn, user):
    create_book(
        db_conn,
        user_id=user.id,
        title="Book A",
        author="Author",
        status="reading",
    )
    create_book(
        db_conn,
        user_id=user.id,
        title="Book B",
        author="Author",
        status="completed",
    )

    books, _ = get_books(db_conn, user_id=user.id, status="reading")

    assert len(books) == 1
    assert books[0].title == "Book A"


def test_get_books_filter_case_insensitive(db_conn, user):
    create_book(
        db_conn,
        user_id=user.id,
        title="HARRY POTTER",
        author="ROWLING",
        status="not_started",
        genre="FANTASY",
    )

    books_by_title, _ = get_books(db_conn, user_id=user.id, title="harry")
    books_by_author, _ = get_books(db_conn, user_id=user.id, author="rowling")
    books_by_genre, _ = get_books(db_conn, user_id=user.id, genre="fantasy")

    assert len(books_by_title) == 1
    assert len(books_by_author) == 1
    assert len(books_by_genre) == 1


def test_get_books_combined_filters(db_conn, user):
    create_book(
        db_conn,
        user_id=user.id,
        title="Dune",
        author="Herbert",
        status="reading",
        genre="Sci-Fi",
    )
    create_book(
        db_conn,
        user_id=user.id,
        title="Foundation",
        author="Asimov",
        status="reading",
        genre="Sci-Fi",
    )
    create_book(
        db_conn,
        user_id=user.id,
        title="The Hobbit",
        author="Tolkien",
        status="reading",
        genre="Fantasy",
    )

    books, _ = get_books(
        db_conn, user_id=user.id, genre="Sci-Fi", status="reading"
    )

    assert len(books) == 2


def test_get_books_no_match_returns_empty(db_conn, user):
    create_book(
        db_conn,
        user_id=user.id,
        title="Dune",
        author="Herbert",
        status="not_started",
    )

    books, _ = get_books(db_conn, user_id=user.id, title="nonexistent")

    assert books == []


# --- get_books pagination ---

def test_get_books_limit(db_conn, user):
    for i in range(5):
        create_book(
            db_conn,
            user_id=user.id,
            title=f"Book {i}",
            author="Author",
            status="not_started",
        )

    books, _ = get_books(db_conn, user_id=user.id, limit=3)

    assert len(books) == 3



def test_get_books_next_token_is_none_on_last_page(db_conn, user):
    for i in range(3):
        create_book(
            db_conn,
            user_id=user.id,
            title=f"Book {i}",
            author="Author",
            status="not_started",
        )

    _, next_token = get_books(db_conn, user_id=user.id, limit=10)

    assert next_token is None


def test_get_books_next_token_fetches_next_page(db_conn, user):
    for i in range(5):
        create_book(
            db_conn,
            user_id=user.id,
            title=f"Book {i}",
            author="Author",
            status="not_started",
        )

    first_page, next_token = get_books(db_conn, user_id=user.id, limit=3)
    second_page, _ = get_books(
        db_conn, user_id=user.id, limit=3, next_token=next_token
    )

    first_ids = {b.id for b in first_page}
    second_ids = {b.id for b in second_page}
    assert first_ids.isdisjoint(second_ids)
    assert len(second_page) == 2


def test_get_books_pagination_covers_all(db_conn, user):
    for i in range(5):
        create_book(
            db_conn,
            user_id=user.id,
            title=f"Book {i}",
            author="Author",
            status="not_started",
        )

    all_ids = set()
    token = None
    while True:
        books, token = get_books(
            db_conn, user_id=user.id, limit=2, next_token=token
        )
        all_ids.update(b.id for b in books)
        if token is None:
            break

    assert len(all_ids) == 5


def test_get_books_pagination_with_filter(db_conn, user):
    for i in range(4):
        create_book(
            db_conn,
            user_id=user.id,
            title=f"Sci-Fi Book {i}",
            author="Author",
            status="not_started",
            genre="Sci-Fi",
        )
    create_book(
        db_conn,
        user_id=user.id,
        title="Fantasy Book",
        author="Author",
        status="not_started",
        genre="Fantasy",
    )

    first_page, next_token = get_books(
        db_conn, user_id=user.id, genre="Sci-Fi", limit=2
    )
    second_page, no_token = get_books(
        db_conn, user_id=user.id, genre="Sci-Fi", limit=2,
        next_token=next_token,
    )

    assert len(first_page) == 2
    assert len(second_page) == 2
    assert no_token is None
    assert all(b.genre == "Sci-Fi" for b in first_page + second_page)


# --- update_book ---

def test_update_book_single_field(db_conn, user, sample_book):
    updated = update_book(
        db_conn, book_id=sample_book.id, user_id=user.id, status="reading"
    )

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


def test_update_book_wrong_user_returns_none(
    db_conn, user, other_user, sample_book
):
    result = update_book(
        db_conn,
        book_id=sample_book.id,
        user_id=other_user.id,
        status="reading",
    )

    assert result is None


def test_update_book_not_found_returns_none(db_conn, user):
    result = update_book(
        db_conn, book_id=999, user_id=user.id, status="reading"
    )

    assert result is None


# --- delete_book ---

def test_delete_book_returns_true(db_conn, user, sample_book):
    result = delete_book(db_conn, book_id=sample_book.id, user_id=user.id)

    assert result is True


def test_delete_book_removes_from_db(db_conn, user, sample_book):
    delete_book(db_conn, book_id=sample_book.id, user_id=user.id)

    found = get_book_by_id(db_conn, book_id=sample_book.id, user_id=user.id)
    assert found is None


def test_delete_book_wrong_user_returns_false(
    db_conn, user, other_user, sample_book
):
    result = delete_book(
        db_conn, book_id=sample_book.id, user_id=other_user.id
    )

    assert result is False


def test_delete_book_wrong_user_does_not_remove(
    db_conn, user, other_user, sample_book
):
    delete_book(db_conn, book_id=sample_book.id, user_id=other_user.id)

    found = get_book_by_id(db_conn, book_id=sample_book.id, user_id=user.id)
    assert found is not None


def test_delete_book_not_found_returns_false(db_conn, user):
    result = delete_book(db_conn, book_id=999, user_id=user.id)

    assert result is False
