import sys
from pathlib import Path


FRONTEND_DIR = Path(__file__).resolve().parents[1] / "src" / "frontend"
if str(FRONTEND_DIR) not in sys.path:
    sys.path.insert(0, str(FRONTEND_DIR))

import app as frontend_app  # noqa: E402


class SessionState(dict):
    def __getattr__(self, name):
        return self[name]

    def __setattr__(self, name, value):
        self[name] = value


class Context:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


class FakeSidebar:
    def __init__(self):
        self.text_values = []
        self.select_value = ""
        self.calls = []

    def header(self, text):
        self.calls.append(("header", text))

    def text_input(self, label):
        self.calls.append(("text_input", label))
        return self.text_values.pop(0)

    def selectbox(self, label, options, format_func):
        self.calls.append(
            ("selectbox", label, options, format_func(self.select_value)),
        )
        return self.select_value


class FakeStreamlit(Context):
    def __init__(self):
        self.session_state = SessionState()
        self.sidebar = FakeSidebar()
        self.text_values = []
        self.number_values = []
        self.select_values = []
        self.submit_values = []
        self.button_values = []
        self.calls = []

    def __getattr__(self, name):
        def recorder(*args, **kwargs):
            self.calls.append((name, args, kwargs))
            return None

        return recorder

    def form(self, *args, **kwargs):
        self.calls.append(("form", args, kwargs))
        return self

    def container(self, *args, **kwargs):
        self.calls.append(("container", args, kwargs))
        return self

    def columns(self, spec):
        self.calls.append(("columns", spec, {}))
        count = spec if isinstance(spec, int) else len(spec)
        return [self for _ in range(count)]

    def tabs(self, labels):
        self.calls.append(("tabs", labels, {}))
        return [self for _ in labels]

    def text_input(self, *args, **kwargs):
        self.calls.append(("text_input", args, kwargs))
        return self.text_values.pop(0)

    def number_input(self, *args, **kwargs):
        self.calls.append(("number_input", args, kwargs))
        return self.number_values.pop(0)

    def selectbox(self, label, options, **kwargs):
        self.calls.append(("selectbox", (label, options), kwargs))
        if self.select_values:
            return self.select_values.pop(0)
        return options[kwargs.get("index", 0)]

    def form_submit_button(self, *args, **kwargs):
        self.calls.append(("form_submit_button", args, kwargs))
        return self.submit_values.pop(0)

    def button(self, *args, **kwargs):
        self.calls.append(("button", args, kwargs))
        return self.button_values.pop(0) if self.button_values else False

    def warning(self, message):
        self.calls.append(("warning", message))

    def success(self, message):
        self.calls.append(("success", message))

    def info(self, message):
        self.calls.append(("info", message))

    def error(self, message):
        self.calls.append(("error", message))

    def rerun(self):
        self.calls.append(("rerun",))


def test_init_session_state_sets_defaults(monkeypatch):
    fake_st = FakeStreamlit()
    monkeypatch.setattr(frontend_app, "st", fake_st)

    frontend_app.init_session_state()

    assert fake_st.session_state == {
        "access_token": None,
        "username": None,
        "is_authenticated": False,
    }


def test_logout_clears_session_and_reruns(monkeypatch):
    fake_st = FakeStreamlit()
    fake_st.session_state.access_token = "jwt"
    fake_st.session_state.username = "alice"
    fake_st.session_state.is_authenticated = True
    monkeypatch.setattr(frontend_app, "st", fake_st)

    frontend_app.logout()

    assert fake_st.session_state.access_token is None
    assert fake_st.session_state.username is None
    assert fake_st.session_state.is_authenticated is False
    assert ("rerun",) in fake_st.calls


def test_filters_sidebar_returns_selected_filters(monkeypatch):
    fake_st = FakeStreamlit()
    fake_st.sidebar.text_values = ["Dune", "Herbert", "Sci-Fi"]
    fake_st.sidebar.select_value = "reading"
    monkeypatch.setattr(frontend_app, "st", fake_st)

    filters = frontend_app.filters_sidebar()

    assert filters == {
        "title": "Dune",
        "author": "Herbert",
        "genre": "Sci-Fi",
        "status": "reading",
    }


def test_add_book_section_warns_when_required_fields_are_missing(monkeypatch):
    fake_st = FakeStreamlit()
    fake_st.text_values = ["", "Herbert", "Sci-Fi"]
    fake_st.number_values = [100, 10]
    fake_st.submit_values = [True]
    monkeypatch.setattr(frontend_app, "st", fake_st)

    frontend_app.add_book_section("jwt")

    assert (
        "warning",
        "Fields 'Title' and 'Author' are mandatory.",
    ) in fake_st.calls


def test_add_book_section_warns_when_current_page_exceeds_total(monkeypatch):
    fake_st = FakeStreamlit()
    fake_st.text_values = ["Dune", "Herbert", "Sci-Fi"]
    fake_st.number_values = [100, 101]
    fake_st.submit_values = [True]
    monkeypatch.setattr(frontend_app, "st", fake_st)

    frontend_app.add_book_section("jwt")

    assert (
        "warning",
        "Current page cannot be bigger than the total amount.",
    ) in fake_st.calls


def test_add_book_section_creates_book(monkeypatch):
    fake_st = FakeStreamlit()
    fake_st.text_values = [" Dune ", " Herbert ", " Sci-Fi "]
    fake_st.number_values = [100, 10]
    fake_st.submit_values = [True]
    created = []
    monkeypatch.setattr(frontend_app, "st", fake_st)
    monkeypatch.setattr(
        frontend_app,
        "create_book",
        lambda token, payload: created.append((token, payload)),
    )

    frontend_app.add_book_section("jwt")

    assert created == [
        (
            "jwt",
            {
                "title": "Dune",
                "author": "Herbert",
                "genre": "Sci-Fi",
                "total_pages": 100,
                "current_page": 10,
                "status": "reading",
            },
        )
    ]
    assert ("success", "Book added.") in fake_st.calls
    assert ("rerun",) in fake_st.calls


def test_render_book_card_updates_book(monkeypatch):
    fake_st = FakeStreamlit()
    fake_st.text_values = [" Dune Messiah ", " Frank Herbert ", ""]
    fake_st.number_values = [300, 300]
    fake_st.submit_values = [True]
    updated = []
    monkeypatch.setattr(frontend_app, "st", fake_st)
    monkeypatch.setattr(
        frontend_app,
        "update_book",
        lambda token, book_id, payload: updated.append(
            (token, book_id, payload),
        ),
    )

    frontend_app.render_book_card(
        "jwt",
        {
            "id": "book-id",
            "title": "Dune",
            "author": "Herbert",
            "genre": None,
            "total_pages": 100,
            "current_page": 50,
            "status": "reading",
        },
    )

    assert updated == [
        (
            "jwt",
            "book-id",
            {
                "title": "Dune Messiah",
                "author": "Frank Herbert",
                "genre": None,
                "total_pages": 300,
                "current_page": 300,
                "status": "reading",
            },
        )
    ]
    assert ("success", "Book updated.") in fake_st.calls


def test_render_book_card_deletes_book(monkeypatch):
    fake_st = FakeStreamlit()
    fake_st.text_values = ["Dune", "Herbert", ""]
    fake_st.number_values = [0, 50]
    fake_st.submit_values = [False]
    fake_st.button_values = [True]
    deleted = []
    monkeypatch.setattr(frontend_app, "st", fake_st)
    monkeypatch.setattr(
        frontend_app,
        "delete_book",
        lambda token, book_id: deleted.append((token, book_id)),
    )

    frontend_app.render_book_card(
        "jwt",
        {
            "id": "book-id",
            "title": "Dune",
            "author": "Herbert",
            "genre": None,
            "total_pages": None,
            "current_page": 50,
            "status": "reading",
        },
    )

    assert deleted == [("jwt", "book-id")]
    assert ("success", "Book deleted.") in fake_st.calls


def test_books_screen_shows_empty_state(monkeypatch):
    fake_st = FakeStreamlit()
    fake_st.session_state.access_token = "jwt"
    fake_st.session_state.username = "alice"
    fake_st.button_values = [False]
    fake_st.sidebar.text_values = ["", "", ""]
    fake_st.sidebar.select_value = ""
    monkeypatch.setattr(frontend_app, "st", fake_st)
    monkeypatch.setattr(frontend_app, "add_book_section", lambda token: None)
    monkeypatch.setattr(frontend_app, "get_books", lambda **kwargs: [])

    frontend_app.books_screen()

    assert ("info", "Books not found.") in fake_st.calls


def test_books_screen_renders_books(monkeypatch):
    fake_st = FakeStreamlit()
    fake_st.session_state.access_token = "jwt"
    fake_st.session_state.username = "alice"
    fake_st.button_values = [False]
    fake_st.sidebar.text_values = ["Dune", "", ""]
    fake_st.sidebar.select_value = "reading"
    rendered = []
    monkeypatch.setattr(frontend_app, "st", fake_st)
    monkeypatch.setattr(frontend_app, "add_book_section", lambda token: None)
    monkeypatch.setattr(
        frontend_app,
        "get_books",
        lambda **kwargs: [{"id": "book-id"}],
    )
    monkeypatch.setattr(
        frontend_app,
        "render_book_card",
        lambda token, book: rendered.append((token, book)),
    )

    frontend_app.books_screen()

    assert rendered == [("jwt", {"id": "book-id"})]


def test_main_routes_to_books_screen_when_authenticated(monkeypatch):
    fake_st = FakeStreamlit()
    fake_st.session_state.access_token = "jwt"
    fake_st.session_state.is_authenticated = True
    calls = []
    monkeypatch.setattr(frontend_app, "st", fake_st)
    monkeypatch.setattr(
        frontend_app,
        "books_screen",
        lambda: calls.append("books"),
    )
    monkeypatch.setattr(
        frontend_app,
        "auth_screen",
        lambda: calls.append("auth"),
    )

    frontend_app.main()

    assert calls == ["books"]


def test_main_routes_to_auth_screen_when_anonymous(monkeypatch):
    fake_st = FakeStreamlit()
    calls = []
    monkeypatch.setattr(frontend_app, "st", fake_st)
    monkeypatch.setattr(
        frontend_app,
        "books_screen",
        lambda: calls.append("books"),
    )
    monkeypatch.setattr(
        frontend_app,
        "auth_screen",
        lambda: calls.append("auth"),
    )

    frontend_app.main()

    assert calls == ["auth"]
