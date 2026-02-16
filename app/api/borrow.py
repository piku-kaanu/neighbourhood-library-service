# app/api/borrow.py

import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.book import Book
from app.models.borrow import BorrowTransaction
from app.models.member import Member
from app.schemas.borrow import BorrowRequest, BorrowTransactionResponse

router = APIRouter(prefix="/api/v1/borrow", tags=["borrow"])

templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")

DEFAULT_PAGE_SIZE = 10


def _get_transaction_with_book_member(
    db: Session, transaction_id: uuid.UUID
) -> Optional[BorrowTransaction]:
    """Load transaction with book and member relationships."""
    return (
        db.query(BorrowTransaction)
        .filter(BorrowTransaction.id == transaction_id)
        .first()
    )


@router.post("/", response_model=BorrowTransactionResponse)
def borrow_book(
    body: BorrowRequest,
    db: Session = Depends(get_db),
):
    """
    Borrow a book for a member.
    Validates: book exists and has available copies; member exists and is active.
    Decrements book.available_copies and creates a BORROWED transaction.
    """
    book = db.query(Book).filter(Book.id == body.book_id).with_for_update().first()
    if not book:
        return JSONResponse(status_code=404, content={"error": "Book not found"})
    if book.available_copies < 1:
        return JSONResponse(
            status_code=422,
            content={"error": "No copies available to borrow."},
        )

    member = db.query(Member).filter(Member.id == body.member_id).first()
    if not member:
        return JSONResponse(status_code=404, content={"error": "Member not found"})
    if not member.is_active:
        return JSONResponse(
            status_code=422,
            content={"error": "Member is not active and cannot borrow."},
        )

    borrowed_at = datetime.utcnow()
    due_date = borrowed_at + timedelta(days=body.loan_days)

    transaction = BorrowTransaction(
        book_id=body.book_id,
        member_id=body.member_id,
        borrowed_at=borrowed_at,
        due_date=due_date,
        status="BORROWED",
    )
    db.add(transaction)
    book.available_copies -= 1
    db.commit()
    db.refresh(transaction)
    return transaction


@router.post("/{transaction_id}/return", response_model=BorrowTransactionResponse)
def return_book(
    transaction_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """
    Return a borrowed book.
    Validates: transaction exists and status is BORROWED.
    Sets returned_at, status=RETURNED, and increments book.available_copies.
    """
    transaction = _get_transaction_with_book_member(db, transaction_id)
    if not transaction:
        return JSONResponse(status_code=404, content={"error": "Transaction not found"})
    if transaction.status != "BORROWED":
        return JSONResponse(
            status_code=422,
            content={"error": f"Transaction is not borrowed (status: {transaction.status})."},
        )

    book = db.query(Book).filter(Book.id == transaction.book_id).with_for_update().first()
    if book:
        book.available_copies += 1

    transaction.returned_at = datetime.utcnow()
    transaction.status = "RETURNED"
    db.commit()
    db.refresh(transaction)
    return transaction


@router.get("/form", response_class=HTMLResponse)
def borrow_form(
    request: Request,
    db: Session = Depends(get_db),
    success: Optional[str] = Query(None),
    due_date: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
):
    """Show the borrow-a-book form. Books with available_copies > 0, active members only."""
    books = db.query(Book).filter(Book.available_copies > 0).order_by(Book.title).all()
    members = db.query(Member).filter(Member.is_active == True).order_by(Member.full_name).all()
    return templates.TemplateResponse(
        request=request,
        name="borrow_form.html",
        context={
            "books": books,
            "members": members,
            "success": success == "1",
            "due_date": due_date or "",
            "error": error,
            "loan_days": 14,
        },
    )


@router.post("/form")
def borrow_submit(
    request: Request,
    db: Session = Depends(get_db),
    book_id: str = Form(...),
    member_id: str = Form(...),
    loan_days: int = Form(14),
):
    """Handle borrow form submission. Redirects back to form with success or error."""
    def redirect_error(msg: str):
        url = str(request.url_for("borrow_form")) + "?" + urlencode({"error": msg})
        return RedirectResponse(url=url, status_code=303)

    try:
        book_uuid = uuid.UUID(book_id)
        member_uuid = uuid.UUID(member_id)
    except ValueError:
        return redirect_error("Invalid book or member.")
    if loan_days < 1 or loan_days > 365:
        return redirect_error("Loan days must be 1–365.")

    book = db.query(Book).filter(Book.id == book_uuid).with_for_update().first()
    if not book:
        return redirect_error("Book not found.")
    if book.available_copies < 1:
        return redirect_error("No copies available.")

    member = db.query(Member).filter(Member.id == member_uuid).first()
    if not member:
        return redirect_error("Member not found.")
    if not member.is_active:
        return redirect_error("Member is not active.")

    borrowed_at = datetime.utcnow()
    due_dt = borrowed_at + timedelta(days=loan_days)
    due_date_str = due_dt.strftime("%Y-%m-%d")

    transaction = BorrowTransaction(
        book_id=book_uuid,
        member_id=member_uuid,
        borrowed_at=borrowed_at,
        due_date=due_dt,
        status="BORROWED",
    )
    db.add(transaction)
    book.available_copies -= 1
    db.commit()

    url = str(request.url_for("borrow_form")) + "?" + urlencode({"success": "1", "due_date": due_date_str})
    return RedirectResponse(url=url, status_code=303)


def _filter_borrow_query(
    db: Session,
    member_id: Optional[uuid.UUID],
    book_id: Optional[uuid.UUID],
    status: Optional[str],
):
    """Build filtered query for borrow transactions."""
    q = db.query(BorrowTransaction)
    if member_id is not None:
        q = q.filter(BorrowTransaction.member_id == member_id)
    if book_id is not None:
        q = q.filter(BorrowTransaction.book_id == book_id)
    if status and status.strip():
        q = q.filter(BorrowTransaction.status == status.strip().upper())
    return q.order_by(BorrowTransaction.borrowed_at.desc())


@router.get("/list", response_class=HTMLResponse)
def borrow_list(
    request: Request,
    db: Session = Depends(get_db),
    member_id: Optional[str] = Query(None),
    book_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=100),
    error: Optional[str] = Query(None),
):
    """List borrow transactions (HTML) with filters and pagination."""
    member_uuid = None
    if member_id and member_id.strip():
        try:
            member_uuid = uuid.UUID(member_id.strip())
        except ValueError:
            pass
    book_uuid = None
    if book_id and book_id.strip():
        try:
            book_uuid = uuid.UUID(book_id.strip())
        except ValueError:
            pass

    q = _filter_borrow_query(db, member_uuid, book_uuid, status)
    total = db.execute(select(func.count()).select_from(q.subquery())).scalar() or 0
    total_pages = (total + per_page - 1) // per_page if total else 1
    page = min(page, total_pages) if total_pages else 1
    offset = (page - 1) * per_page
    transactions = (
        q.offset(offset)
        .limit(per_page)
        .options(
            joinedload(BorrowTransaction.book),
            joinedload(BorrowTransaction.member),
        )
        .all()
    )

    members = db.query(Member).order_by(Member.full_name).all()
    books = db.query(Book).order_by(Book.title).all()

    pagination_params = {"per_page": per_page}
    if member_id:
        pagination_params["member_id"] = member_id
    if book_id:
        pagination_params["book_id"] = book_id
    if status:
        pagination_params["status"] = status
    pagination_query = urlencode(pagination_params)

    return templates.TemplateResponse(
        request=request,
        name="borrow_list.html",
        context={
            "transactions": transactions,
            "members": members,
            "books": books,
            "filter_member_id": member_id or "",
            "filter_book_id": book_id or "",
            "filter_status": status or "all",
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "pagination_query": pagination_query,
            "error": error,
        },
    )


@router.post("/{transaction_id}/return/form")
def borrow_return_form(
    transaction_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
):
    """Return a book (form POST). Redirects to borrow list."""
    transaction = _get_transaction_with_book_member(db, transaction_id)
    if not transaction:
        url = str(request.url_for("borrow_list")) + "?" + urlencode({"error": "Transaction not found"})
        return RedirectResponse(url=url, status_code=303)
    if transaction.status != "BORROWED":
        url = str(request.url_for("borrow_list")) + "?" + urlencode({"error": "Already returned"})
        return RedirectResponse(url=url, status_code=303)

    book = db.query(Book).filter(Book.id == transaction.book_id).with_for_update().first()
    if book:
        book.available_copies += 1
    transaction.returned_at = datetime.utcnow()
    transaction.status = "RETURNED"
    db.commit()

    return RedirectResponse(url=request.url_for("borrow_list"), status_code=303)


@router.get("/", response_model=list[BorrowTransactionResponse])
def list_transactions(
    db: Session = Depends(get_db),
    member_id: Optional[uuid.UUID] = Query(None),
    book_id: Optional[uuid.UUID] = Query(None),
    status: Optional[str] = Query(None),
):
    """
    List borrow transactions with optional filters: member_id, book_id, status.
    """
    q = _filter_borrow_query(db, member_id, book_id, status)
    return q.all()
