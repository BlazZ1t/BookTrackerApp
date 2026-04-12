from typing import Any

import streamlit as st

from api import (
    APIError,
    create_book,
    delete_book,
    get_books,
    login,
    register,
    update_book,
)
from constants import API_BASE_URL, BOOK_STATUS_OPTIONS
from ui_helpers import (
    calculate_progress,
    human_status,
    show_api_error,
    suggest_status,
)


st.set_page_config(
    page_title="Book Tracker",
    page_icon="📚",
    layout="wide",
)


def init_session_state() -> None:
    if "access_token" not in st.session_state:  # nosec B105
        st.session_state["access_token"] = None
    if "username" not in st.session_state:
        st.session_state["username"] = None
    if "is_authenticated" not in st.session_state:
        st.session_state["is_authenticated"] = False


def logout() -> None:
    st.session_state.access_token = None
    st.session_state.username = None
    st.session_state.is_authenticated = False
    st.rerun()


def _handle_login_submit(username: str, password: str) -> None:
    if not username or not password:
        st.warning("Fill out username and password.")
        return

    try:
        token = login(username, password)
        st.session_state["access_token"] = token
        st.session_state["username"] = username
        st.session_state["is_authenticated"] = True
        st.success("Successful log in.")
        st.rerun()
    except APIError as exc:
        show_api_error(str(exc))


def _handle_register_submit(username: str, password: str) -> None:
    if not username or not password:
        st.warning("Fill out username and password.")
        return

    try:
        register(username, password)
        st.success("Successfully signed up. Now you can log in.")
    except APIError as exc:
        show_api_error(str(exc))


def auth_screen() -> None:
    st.title("📚 Book Tracker")
    st.caption(f"Backend API: {API_BASE_URL}")

    tab_login, tab_register = st.tabs(["Log in", "Sign up"])

    with tab_login:
        with st.form("login_form"):
            username = st.text_input("Username", key="login_username")
            password = st.text_input(
                "Password",
                type="password",
                key="login_password",
            )
            submit_login = st.form_submit_button(
                "Log in",
                use_container_width=True,
            )

        if submit_login:
            _handle_login_submit(username, password)

    with tab_register:
        with st.form("register_form"):
            username = st.text_input("Username", key="register_username")
            password = st.text_input(
                "Password",
                type="password",
                key="register_password",
            )
            submit_register = st.form_submit_button(
                "Sign up",
                use_container_width=True,
            )

        if submit_register:
            _handle_register_submit(username, password)


def _build_book_payload(
    title: str,
    author: str,
    genre: str,
    total_pages_input: int,
    current_page: int,
    status: str,
) -> dict[str, Any] | None:
    if not title.strip() or not author.strip():
        st.warning("Fields 'Title' and 'Author' are mandatory.")
        return None

    total_pages = total_pages_input if total_pages_input > 0 else None
    if total_pages is not None and current_page > total_pages:
        st.warning("Current page cannot be bigger than the total amount.")
        return None

    return {
        "title": title.strip(),
        "author": author.strip(),
        "genre": genre.strip() or None,
        "total_pages": total_pages,
        "current_page": int(current_page),
        "status": status,
    }


def add_book_section(token: str) -> None:
    st.subheader("Add a book")

    with st.form("add_book_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("Title *")
            author = st.text_input("Author *")
            genre = st.text_input("Genre")
        with col2:
            total_pages_input = st.number_input(
                "Pages total", min_value=0, step=1, value=0)
            current_page = st.number_input(
                "Current page", min_value=0, step=1, value=0)

        suggested = suggest_status(
            current_page,
            total_pages_input if total_pages_input > 0 else None,
        )
        status = st.selectbox(
            "Status",
            options=BOOK_STATUS_OPTIONS,
            index=BOOK_STATUS_OPTIONS.index(suggested),
            format_func=human_status,
        )

        submit = st.form_submit_button("Add", use_container_width=True)

    if not submit:
        return

    payload = _build_book_payload(
        title=title,
        author=author,
        genre=genre,
        total_pages_input=int(total_pages_input),
        current_page=int(current_page),
        status=status,
    )
    if payload is None:
        return

    try:
        create_book(token, payload)
        st.success("Book added.")
        st.rerun()
    except APIError as exc:
        show_api_error(str(exc))


def filters_sidebar() -> dict:
    st.sidebar.header("Search & Filters")
    title_filter = st.sidebar.text_input("Title")
    author_filter = st.sidebar.text_input("Author")
    genre_filter = st.sidebar.text_input("Genre")

    status_options = [""] + BOOK_STATUS_OPTIONS
    status_filter = st.sidebar.selectbox(
        "Status",
        options=status_options,
        format_func=(
            lambda value: "All" if value == "" else human_status(value)
        ),
    )

    return {
        "title": title_filter,
        "author": author_filter,
        "genre": genre_filter,
        "status": status_filter,
    }


def _extract_book_fields(book: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": book.get("id"),
        "title": book.get("title", "No title"),
        "author": book.get("author", "Unknown author"),
        "genre": book.get("genre") or "—",
        "total_pages": book.get("total_pages"),
        "current_page": book.get("current_page", 0),
        "status": book.get("status", "not_started"),
    }


def _render_book_info(book_data: dict[str, Any]) -> None:
    progress = calculate_progress(
        book_data["current_page"], book_data["total_pages"])

    st.markdown(f"### {book_data['title']}")
    st.write(f"**Author:** {book_data['author']}")
    st.write(f"**Genre:** {book_data['genre']}")
    st.write(f"**Status:** {human_status(book_data['status'])}")

    if book_data["total_pages"]:
        st.write(
            f"**Pages:** {book_data['current_page']} / "
            f"{book_data['total_pages']}"
        )
        st.progress(progress / 100)
        st.caption(f"Progress: {progress:.2f}%")
    else:
        st.write(f"**Current page:** {book_data['current_page']}")
        st.caption("Total amount is unknown")


def _render_update_form(
        book_data: dict[str, Any]) -> tuple[bool, dict[str, Any] | None]:
    book_id = book_data["id"]

    with st.form(f"update_book_{book_id}"):
        st.markdown("**Update the book**")

        new_title = st.text_input(
            "Title", value=book_data["title"], key=f"title_{book_id}")
        new_author = st.text_input(
            "Author", value=book_data["author"], key=f"author_{book_id}")
        new_genre = st.text_input(
            "Genre",
            value="" if book_data["genre"] == "—" else book_data["genre"],
            key=f"genre_{book_id}",
        )

        new_total_pages_raw = st.number_input(
            "Pages total",
            min_value=0,
            step=1,
            value=int(book_data["total_pages"] or 0),
            key=f"total_pages_{book_id}",
        )

        new_current_page = st.number_input(
            "Current page",
            min_value=0,
            step=1,
            value=int(book_data["current_page"]),
            key=f"current_page_{book_id}",
        )

        suggested = suggest_status(
            int(new_current_page),
            int(new_total_pages_raw) if new_total_pages_raw > 0 else None,
        )
        default_status = (
            book_data["status"]
            if book_data["status"] in BOOK_STATUS_OPTIONS
            else suggested
        )

        new_status = st.selectbox(
            "Status",
            options=BOOK_STATUS_OPTIONS,
            index=BOOK_STATUS_OPTIONS.index(default_status),
            format_func=human_status,
            key=f"status_{book_id}",
        )

        save_clicked = st.form_submit_button("Save", use_container_width=True)

    if not save_clicked:
        return False, None

    payload = _build_book_payload(
        title=new_title,
        author=new_author,
        genre=new_genre,
        total_pages_input=int(new_total_pages_raw),
        current_page=int(new_current_page),
        status=new_status,
    )
    return True, payload


def _handle_update_book(
        token: str, book_id: str, payload: dict[str, Any] | None) -> None:
    if payload is None:
        return

    try:
        update_book(token, book_id, payload)
        st.success("Book updated.")
        st.rerun()
    except APIError as exc:
        show_api_error(str(exc))


def _handle_delete_book(token: str, book_id: str) -> None:
    try:
        delete_book(token, book_id)
        st.success("Book deleted.")
        st.rerun()
    except APIError as exc:
        show_api_error(str(exc))


def render_book_card(token: str, book: dict[str, Any]) -> None:
    book_data = _extract_book_fields(book)

    with st.container(border=True):
        col_info, col_actions = st.columns([2, 1])

        with col_info:
            _render_book_info(book_data)

        with col_actions:
            save_clicked, payload = _render_update_form(book_data)

            if save_clicked:
                _handle_update_book(token, book_data["id"], payload)

            if st.button(
                "Delete",
                key=f"delete_{book_data['id']}",
                use_container_width=True,
            ):
                _handle_delete_book(token, book_data["id"])


def books_screen() -> None:
    token = st.session_state.access_token
    username = st.session_state.username

    st.title("📚 My Books")

    top_col1, top_col2 = st.columns([4, 1])
    with top_col1:
        st.caption(f"Hi, **{username}**")
    with top_col2:
        if st.button("Log out", use_container_width=True):
            logout()

    filters = filters_sidebar()

    add_book_section(token)

    st.divider()
    st.subheader("Book list")

    try:
        books = get_books(
            token=token,
            title=filters["title"],
            author=filters["author"],
            genre=filters["genre"],
            status=filters["status"],
        )
    except APIError as exc:
        show_api_error(str(exc))
        return

    if not books:
        st.info("Books not found.")
        return

    for book in books:
        render_book_card(token, book)


def main() -> None:
    init_session_state()

    if st.session_state.is_authenticated and st.session_state.access_token:
        books_screen()
    else:
        auth_screen()


if __name__ == "__main__":
    main()
