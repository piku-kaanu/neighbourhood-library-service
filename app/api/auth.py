# app/api/auth.py

from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.auth import ROLE_MEMBER, SESSION_USER_ID_KEY, verify_password
from app.database import get_db
from app.models.user import User

router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    """Show login form."""
    return templates.TemplateResponse(request=request, name="login.html", context={"error": None})


@router.post("/login")
def login_submit(
    request: Request,
    db: Session = Depends(get_db),
    username: str = Form(""),
    password: str = Form(""),
):
    if not username or not password:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"error": "Username and password are required."},
            status_code=400,
        )
    user = db.query(User).filter(User.username == username.strip()).first()
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"error": "Invalid username or password."},
            status_code=401,
        )
    request.session[SESSION_USER_ID_KEY] = str(user.id)
    if user.role == ROLE_MEMBER:
        return RedirectResponse(url=str(request.url_for("books_list")), status_code=302)
    return RedirectResponse(url=str(request.url_for("index")), status_code=302)


@router.post("/logout")
def logout(request: Request):
    """Clear session and redirect to login."""
    request.session.clear()
    return RedirectResponse(url=str(request.url_for("login")), status_code=302)
