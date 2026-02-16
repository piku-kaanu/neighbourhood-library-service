# app/main.py

from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from app.api import auth as auth_router
from app.api import books as books_router
from app.api import borrow as borrow_router
from app.api import members as members_router
from app.api.books import filter_books_query
from app.config import settings
from app.core.auth import get_current_user
from app.database import get_db
from app.models.book import Book

app = FastAPI(
    title="Neighborhood Library Service",
    description="API for managing books, members, and lending.",
    version="1.0.0",
)


async def add_user_to_request(request: Request, call_next):
    """Set request.state.user from session so templates can use it."""
    from app.core.auth import get_current_user_id
    from app.database import SessionLocal
    user_id = get_current_user_id(request)
    request.state.user = None
    if user_id:
        import uuid
        db = SessionLocal()
        try:
            from app.models.user import User
            uid = uuid.UUID(user_id)
            request.state.user = db.query(User).filter(User.id == uid).first()
        except (ValueError, TypeError):
            pass
        finally:
            db.close()
    return await call_next(request)


# Order matters: last added runs first. SessionMiddleware must run before add_user_to_request
# so request.session is available. So we add our middleware first, then SessionMiddleware.
app.middleware("http")(add_user_to_request)
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

app.include_router(auth_router.router)
app.include_router(books_router.router)
app.include_router(members_router.router)
app.include_router(borrow_router.router)


@app.get("/", response_class=HTMLResponse)
def index(request: Request, user=Depends(get_current_user)):
    """Serve the main index page. Public; nav varies by login/role."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"user": user, "error": request.query_params.get("error")},
    )


@app.get("/health")
@app.get("/api/v1/health")
def healthcheck():
    """Health check for load balancers and container orchestration."""
    return {"status": "ok"}

