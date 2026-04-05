from dataclasses import dataclass
from typing import Optional


@dataclass
class BookRecord:
    id: int
    user_id: int
    title: str
    author: str
    genre: Optional[str]
    total_pages: Optional[int]
    current_page: int
    status: str

    def progress_percent(self) -> Optional[float]:
        if not self.total_pages:
            return None
        return round(self.current_page / self.total_pages * 100, 2)
