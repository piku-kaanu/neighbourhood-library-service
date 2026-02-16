# app/schemas/book.py

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BookResponse(BaseModel):
    """Schema for a book in list/detail responses."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    author: str
    isbn: str | None
    published_year: int | None
    total_copies: int
    available_copies: int
    created_at: datetime
    updated_at: datetime
