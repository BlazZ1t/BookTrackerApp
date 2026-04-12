import streamlit as st

from frontend.api import (
    APIError,
    create_book,
    delete_book,
    get_books,
    login,
    register,
    update_book,
)
from frontend.constants import API_BASE_URL, BOOK_STATUS_OPTIONS
from frontend.ui_helpers import calculate_progress, human_status, show_api_error, suggest_status


st.set_page_config(
    page_title="Book Tracker",
    page_icon="📚",
    layout="wide",
)


def init_session_state() -> None:
    defaults = {
        "access_token": None,
        "username": None,
        "is_authenticated": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def logout() -> None:
    st.session_state.access_token = None
    st.session_state.username = None
    st.session_state.is_authenticated = False
    st.rerun()


def auth_screen() -> None:
    st.title("📚 Book Tracker")
    st.caption(f"Backend API: {API_BASE_URL}")

    tab_login, tab_register = st.tabs(["Log in", "Sign up"])

    with tab_login:
        with st.form("login_form"):
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            submit_login = st.form_submit_button("Log in", use_container_width=True)

        if submit_login:
            if not username or not password:
                st.warning("Fill out username and password.")
            else:
                try:
                    token = login(username, password)
                    st.session_state.access_token = token
                    st.session_state.username = username
                    st.session_state.is_authenticated = True
                    st.success("Successful log in.")
                    st.rerun()
                except APIError as exc:
                    show_api_error(str(exc))

    with tab_register:
        with st.form("register_form"):
            username = st.text_input("Username", key="register_username")
            password = st.text_input("Password", type="password", key="register_password")
            submit_register = st.form_submit_button("Sign up", use_container_width=True)

        if submit_register:
            if not username or not password:
                st.warning("Fill our username and password.")
            else:
                try:
                    register(username, password)
                    st.success("Succeccfully signed up. Now you can log in")
                except APIError as exc:
                    show_api_error(str(exc))


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
                "Pages total",
                min_value=0,
                step=1,
                value=0,
            )
            current_page = st.number_input(
                "Current page",
                min_value=0,
                step=1,
                value=0,
            )

        suggested = suggest_status(current_page, total_pages_input if total_pages_input > 0 else None)
        status = st.selectbox(
            "Status",
            options=BOOK_STATUS_OPTIONS,
            index=BOOK_STATUS_OPTIONS.index(suggested),
            format_func=human_status,
        )

        submit = st.form_submit_button("Add", use_container_width=True)

    if submit:
        if not title.strip() or not author.strip():
            st.warning("Fields 'Title' and 'Author' are mandatory.")
            return

        total_pages = total_pages_input if total_pages_input > 0 else None

        if total_pages is not None and current_page > total_pages:
            st.warning("Current page cannot be bigger than the total amount.")
            return

        payload = {
            "title": title.strip(),
            "author": author.strip(),
            "genre": genre.strip() or None,
            "total_pages": total_pages,
            "current_page": int(current_page),
            "status": status,
        }

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
        format_func=lambda value: "All" if value == "" else human_status(value),
    )

    return {
        "title": title_filter,
        "author": author_filter,
        "genre": genre_filter,
        "status": status_filter,
    }


def render_book_card(token: str, book: dict) -> None:
    title = book.get("title", "No title")
    author = book.get("author", "Unknown author")
    genre = book.get("genre") or "—"
    total_pages = book.get("total_pages")
    current_page = book.get("current_page", 0)
    status = book.get("status", "not_started")
    book_id = book.get("id")

    progress = calculate_progress(current_page, total_pages)

    with st.container(border=True):
        col_info, col_actions = st.columns([2, 1])

        with col_info:
            st.markdown(f"### {title}")
            st.write(f"**Author:** {author}")
            st.write(f"**Genre:** {genre}")
            st.write(f"**Status:** {human_status(status)}")
            if total_pages:
                st.write(f"**Pages:** {current_page} / {total_pages}")
                st.progress(progress / 100)
                st.caption(f"Progress: {progress:.2f}%")
            else:
                st.write(f"**Current page:** {current_page}")
                st.caption("Total amount is unknown")

        with col_actions:
            with st.form(f"update_book_{book_id}"):
                st.markdown("**Update the book**")

                new_title = st.text_input("Title", value=title, key=f"title_{book_id}")
                new_author = st.text_input("Author", value=author, key=f"author_{book_id}")
                new_genre = st.text_input(
                    "Genre",
                    value="" if genre == "—" else genre,
                    key=f"genre_{book_id}",
                )

                new_total_pages_raw = st.number_input(
                    "Pages total",
                    min_value=0,
                    step=1,
                    value=int(total_pages or 0),
                    key=f"total_pages_{book_id}",
                )

                new_current_page = st.number_input(
                    "Current page",
                    min_value=0,
                    step=1,
                    value=int(current_page),
                    key=f"current_page_{book_id}",
                )

                suggested = suggest_status(
                    int(new_current_page),
                    int(new_total_pages_raw) if new_total_pages_raw > 0 else None,
                )
                new_status = st.selectbox(
                    "Status",
                    options=BOOK_STATUS_OPTIONS,
                    index=BOOK_STATUS_OPTIONS.index(suggested if status not in BOOK_STATUS_OPTIONS else status),
                    format_func=human_status,
                    key=f"status_{book_id}",
                )

                save_clicked = st.form_submit_button("Save", use_container_width=True)

            if save_clicked:
                new_total_pages = int(new_total_pages_raw) if new_total_pages_raw > 0 else None

                if new_total_pages is not None and new_current_page > new_total_pages:
                    st.warning("Current page cannot be bigger than the total amount.")
                    return

                payload = {
                    "title": new_title.strip(),
                    "author": new_author.strip(),
                    "genre": new_genre.strip() or None,
                    "total_pages": new_total_pages,
                    "current_page": int(new_current_page),
                    "status": new_status,
                }

                try:
                    update_book(token, book_id, payload)
                    st.success("Book updated.")
                    st.rerun()
                except APIError as exc:
                    show_api_error(str(exc))

            if st.button("Delete", key=f"delete_{book_id}", use_container_width=True):
                try:
                    delete_book(token, book_id)
                    st.success("Book deleted.")
                    st.rerun()
                except APIError as exc:
                    show_api_error(str(exc))


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