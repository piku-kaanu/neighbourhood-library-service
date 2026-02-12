# app/models/borrow.py

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class BorrowTransaction(Base):
    __tablename__ = "borrow_transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    book_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
    )

    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("members.id", ondelete="CASCADE"),
        nullable=False,
    )

    borrowed_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    due_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    returned_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="BORROWED",
        nullable=False,
    )

    # Relationships
    book = relationship("Book", back_populates="borrow_transactions")
    member = relationship("Member", back_populates="borrow_transactions")

    __table_args__ = (
        Index("idx_borrow_member_id", "member_id"),
        Index("idx_borrow_book_id", "book_id"),
        Index("idx_borrow_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<BorrowTransaction(id={self.id}, status={self.status})>"
