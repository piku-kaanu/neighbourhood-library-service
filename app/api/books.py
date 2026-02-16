# app/api/books.py

import uuid
from pathlib import Path
from typing import Optional

from fastapi import Depends, APIRouter, Form, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.auth import require_member_or_admin, require_super_admin
from app.database import get_db
from app.models.book import Book
from app.models.user import User

router = APIRouter(prefix="/api/v1/books", tags=["books"])

templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")


def filter_books_query(db: Session, title: Optional[str], author: Optional[str], year: Optional[int], available: Optional[str]):
    """Build filtered query for books. available: 'true' = available only, 'false' = unavailable only, else all."""
    q = db.query(Book)
    if title and title.strip():
        q = q.filter(Book.title.ilike(f"%{title.strip()}%"))
    if author and author.strip():
        q = q.filter(Book.author.ilike(f"%{author.strip()}%"))
    if year is not None:
        q = q.filter(Book.published_year == year)
    if available == "true" or available == "yes":
        q = q.filter(Book.available_copies > 0)
    elif available == "false" or available == "no":
        q = q.filter(Book.available_copies == 0)
    return q.order_by(Book.title)


@router.get("/", response_class=HTMLResponse)
def books_list(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_member_or_admin),
    title: Optional[str] = Query(None),
    author: Optional[str] = Query(None),
    year: Optional[str] = Query(None),
    available: Optional[str] = Query(None),
):
    """List all books (HTML page) with optional filters."""
    # Parse year: empty string or None -> None, otherwise try to convert to int
    year_int = None
    if year and year.strip():
        try:
            year_int = int(year.strip())
        except ValueError:
            pass  # Invalid year, treat as None
    
    books = filter_books_query(db, title, author, year_int, available).all()
    return templates.TemplateResponse(
        request=request,
        name="books_list.html",
        context={
            "books": books,
            "filter_title": title or "",
            "filter_author": author or "",
            "filter_year": year if year is not None else "",
            "filter_available": available or "all",
            "user": user,
        },
    )


@router.get("/new", response_class=HTMLResponse)
def book_new(request: Request, user: User = Depends(require_super_admin)):
    """Show add-book form."""
    return templates.TemplateResponse(
        request=request,
        name="book_form.html",
        context={"errors": None},
    )


@router.post("/")
def book_create(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_super_admin),
    title: str = Form(...),
    author: str = Form(...),
    isbn: str = Form(...),
    published_year: int = Form(...),
    total_copies: int = Form(...),
    available_copies: int = Form(...),
):
    """Create a book from form. Redirect to list on success; re-show form with errors otherwise."""
    errors = {}
    if not title or not title.strip():
        errors["title"] = "Title is required."
    if not author or not author.strip():
        errors["author"] = "Author is required."
    if not isbn or not isbn.strip():
        errors["isbn"] = "ISBN is required."
    if published_year is None or published_year < 1 or published_year > 9999:
        errors["published_year"] = "Published year must be between 1 and 9999."
    if total_copies is None or total_copies < 1:
        errors["total_copies"] = "Total copies must be at least 1."
    if available_copies is None or available_copies < 0:
        errors["available_copies"] = "Available copies must be 0 or more."
    if not errors and available_copies > total_copies:
        errors["available_copies"] = "Available copies cannot exceed total copies."

    if errors:
        return templates.TemplateResponse(
            request=request,
            name="book_form.html",
            context={
                "errors": errors,
                "title": title.strip() if title else "",
                "author": author.strip() if author else "",
                "isbn": isbn.strip() if isbn else "",
                "published_year": published_year,
                "total_copies": total_copies,
                "available_copies": available_copies,
            },
            status_code=422,
        )

    book = Book(
        title=title.strip(),
        author=author.strip(),
        isbn=isbn.strip() or None,
        published_year=published_year,
        total_copies=total_copies,
        available_copies=available_copies,
    )
    db.add(book)
    db.commit()
    return RedirectResponse(url=request.url_for("books_list"), status_code=303)


@router.put("/{book_id}")
def book_update(
    book_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_super_admin),
    title: str = Form(...),
    author: str = Form(...),
    isbn: str = Form(...),
    published_year: int = Form(...),
    total_copies: int = Form(...),
    available_copies: int = Form(...),
):
    """Update a book. Returns JSON for inline save."""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        return JSONResponse(status_code=404, content={"error": "Book not found"})
    errors = {}
    if not title or not title.strip():
        errors["title"] = "Title is required."
    if not author or not author.strip():
        errors["author"] = "Author is required."
    if not isbn or not isbn.strip():
        errors["isbn"] = "ISBN is required."
    if published_year is None or published_year < 1 or published_year > 9999:
        errors["published_year"] = "Published year must be between 1 and 9999."
    if total_copies is None or total_copies < 1:
        errors["total_copies"] = "Total copies must be at least 1."
    if available_copies is None or available_copies < 0:
        errors["available_copies"] = "Available copies must be 0 or more."
    if not errors and available_copies > total_copies:
        errors["available_copies"] = "Available copies cannot exceed total copies."
    if errors:
        return JSONResponse(status_code=422, content={"errors": errors})

    book.title = title.strip()
    book.author = author.strip()
    book.isbn = isbn.strip() or None
    book.published_year = published_year
    book.total_copies = total_copies
    book.available_copies = available_copies
    db.commit()
    db.refresh(book)
    return JSONResponse(status_code=200, content={
        "id": str(book.id),
        "title": book.title,
        "author": book.author,
        "isbn": book.isbn,
        "published_year": book.published_year,
        "total_copies": book.total_copies,
        "available_copies": book.available_copies,
    })


@router.delete("/{book_id}")
def book_delete(book_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(require_super_admin)):
    """Delete a book."""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        return JSONResponse(status_code=404, content={"error": "Book not found"})
    db.delete(book)
    db.commit()
    return JSONResponse(status_code=200, content={"ok": True})
