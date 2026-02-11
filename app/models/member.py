# app/models/member.py

import uuid
from datetime import datetime, date

from sqlalchemy import String, Boolean, Date, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Member(Base):
    __tablename__ = "members"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    phone: Mapped[str | None] = mapped_column(String(20))

    membership_date: Mapped[date] = mapped_column(
        Date,
        default=date.today,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    borrow_transactions = relationship(
        "BorrowTransaction",
        back_populates="member",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_members_email", "email"),
    )

    def __repr__(self) -> str:
        return f"<Member(id={self.id}, name={self.full_name})>"
