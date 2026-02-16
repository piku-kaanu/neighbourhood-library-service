# app/main.py

from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.api import books as books_router
from app.api import borrow as borrow_router
from app.api import members as members_router
from app.api.books import filter_books_query
from app.database import get_db
from app.models.book import Book

app = FastAPI(
    title="Neighborhood Library Service",
    description="API for managing books, members, and lending.",
    version="1.0.0",
)

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

app.include_router(books_router.router)
app.include_router(members_router.router)
app.include_router(borrow_router.router)


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """Serve the main index page."""
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/health")
@app.get("/api/v1/health")
def healthcheck():
    """Health check for load balancers and container orchestration."""
    return {"status": "ok"}

