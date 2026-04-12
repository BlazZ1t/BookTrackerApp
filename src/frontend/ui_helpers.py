import streamlit as st

from constants import BOOK_STATUSES


def human_status(status: str) -> str:
    return BOOK_STATUSES.get(status, status)


def calculate_progress(current_page: int, total_pages: int | None) -> float:
    if not total_pages or total_pages <= 0:
        return 0.0
    progress = (current_page / total_pages) * 100
    return max(0.0, min(progress, 100.0))


def suggest_status(current_page: int, total_pages: int | None) -> str:
    if not total_pages or total_pages <= 0:
        return "not_started" if current_page == 0 else "reading"

    if current_page <= 0:
        return "not_started"
    if current_page >= total_pages:
        return "completed"
    return "reading"


def show_api_error(message: str) -> None:
    st.error(f"API Error: {message}")
