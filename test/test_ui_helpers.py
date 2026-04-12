import sys
from pathlib import Path


FRONTEND_DIR = Path(__file__).resolve().parents[1] / "src" / "frontend"
if str(FRONTEND_DIR) not in sys.path:
    sys.path.insert(0, str(FRONTEND_DIR))

import ui_helpers  # noqa: E402


def test_human_status_known_status():
    assert ui_helpers.human_status("reading") == "Reading"


def test_human_status_unknown_status_returns_original_value():
    assert ui_helpers.human_status("paused") == "paused"


def test_calculate_progress_without_total_pages_returns_zero():
    assert ui_helpers.calculate_progress(current_page=12, total_pages=None) == 0.0
    assert ui_helpers.calculate_progress(current_page=12, total_pages=0) == 0.0


def test_calculate_progress_returns_percent():
    assert ui_helpers.calculate_progress(current_page=25, total_pages=100) == 25.0


def test_calculate_progress_clamps_to_valid_range():
    assert ui_helpers.calculate_progress(current_page=-5, total_pages=100) == 0.0
    assert ui_helpers.calculate_progress(current_page=150, total_pages=100) == 100.0


def test_suggest_status_without_total_pages():
    assert ui_helpers.suggest_status(current_page=0, total_pages=None) == "not_started"
    assert ui_helpers.suggest_status(current_page=3, total_pages=None) == "reading"
    assert ui_helpers.suggest_status(current_page=0, total_pages=0) == "not_started"
    assert ui_helpers.suggest_status(current_page=3, total_pages=0) == "reading"


def test_suggest_status_with_total_pages():
    assert ui_helpers.suggest_status(current_page=0, total_pages=100) == "not_started"
    assert ui_helpers.suggest_status(current_page=50, total_pages=100) == "reading"
    assert ui_helpers.suggest_status(current_page=100, total_pages=100) == "completed"
    assert ui_helpers.suggest_status(current_page=101, total_pages=100) == "completed"


def test_show_api_error_calls_streamlit_error(monkeypatch):
    calls = []

    monkeypatch.setattr(ui_helpers.st, "error", calls.append)

    ui_helpers.show_api_error("Something went wrong")

    assert calls == ["API Error: Something went wrong"]
