from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class BookStatus(str, Enum):
    not_started = "not_started"
    reading = "reading"
    completed = "completed"


class CreateBookRequest(BaseModel):
    title: str
    author: str
    genre: Optional[str] = None
    total_pages: Optional[int] = Field(None, gt=0)
    current_page: int = Field(0, ge=0)
    status: BookStatus


class UpdateBookRequest(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    genre: Optional[str] = None
    total_pages: Optional[int] = Field(None, gt=0)
    current_page: Optional[int] = Field(None, ge=0)
    status: Optional[BookStatus] = None


class BookResponse(BaseModel):
    id: str
    user_id: str
    title: str
    author: str
    genre: Optional[str]
    total_pages: Optional[int]
    current_page: int
    status: BookStatus
    progress_percent: Optional[float]


class BookListResponse(BaseModel):
    books: list[BookResponse]
    next_token: Optional[str]
