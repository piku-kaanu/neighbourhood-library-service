# app/api/auth.py

from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.auth import (
    ROLE_MEMBER,
    SESSION_USER_ID_KEY,
    get_current_user_required,
    hash_password,
    verify_password,
)
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
    return RedirectResponse(url=str(request.url_for("login_page")), status_code=302)


@router.get("/change-password", response_class=HTMLResponse)
def change_password_page(
    request: Request,
    user: User = Depends(get_current_user_required),
):
    """Show change-password form for logged-in users."""
    return templates.TemplateResponse(
        request=request,
        name="change_password.html",
        context={"user": user, "error": None, "success": request.query_params.get("updated")},
    )


@router.post("/change-password")
def change_password_submit(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_required),
    current_password: str = Form(""),
    new_password: str = Form(""),
    new_password_confirm: str = Form(""),
):
    """Update password after verifying current password and matching new/confirm."""
    if not current_password:
        return templates.TemplateResponse(
            request=request,
            name="change_password.html",
            context={"user": user, "error": "Current password is required.", "success": None},
            status_code=400,
        )
    if not verify_password(current_password, user.password_hash):
        return templates.TemplateResponse(
            request=request,
            name="change_password.html",
            context={"user": user, "error": "Current password is incorrect.", "success": None},
            status_code=401,
        )
    if not new_password or len(new_password.strip()) < 1:
        return templates.TemplateResponse(
            request=request,
            name="change_password.html",
            context={"user": user, "error": "New password is required.", "success": None},
            status_code=400,
        )
    if new_password != new_password_confirm:
        return templates.TemplateResponse(
            request=request,
            name="change_password.html",
            context={"user": user, "error": "New password and confirmation do not match.", "success": None},
            status_code=400,
        )
    user.password_hash = hash_password(new_password)
    db.add(user)
    db.commit()
    return RedirectResponse(
        url=str(request.url_for("change_password_page")) + "?updated=1",
        status_code=302,
    )
