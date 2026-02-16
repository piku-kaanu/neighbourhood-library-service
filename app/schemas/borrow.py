# app/schemas/borrow.py

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BorrowRequest(BaseModel):
    """Request body for borrowing a book."""

    book_id: uuid.UUID = Field(..., description="ID of the book to borrow")
    member_id: uuid.UUID = Field(..., description="ID of the member borrowing")
    loan_days: int = Field(14, ge=1, le=365, description="Number of days until due (default 14)")


class BorrowTransactionResponse(BaseModel):
    """Response schema for a borrow transaction."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    book_id: uuid.UUID
    member_id: uuid.UUID
    borrowed_at: datetime
    due_date: datetime
    returned_at: datetime | None
    status: str
