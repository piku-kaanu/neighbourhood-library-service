# app/core/auth.py

import uuid
from typing import Annotated

from fastapi import Depends, Request
from fastapi.responses import RedirectResponse
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bcrypt limit (72 bytes); we always truncate so the backend never sees more
BCRYPT_MAX_PASSWORD_BYTES = 72


def _to_safe_bcrypt_bytes(password: str) -> bytes:
    """Return at most 72 bytes (bcrypt limit). Pass this to passlib to avoid encoding issues."""
    raw = (password or " ").encode("utf-8")[:BCRYPT_MAX_PASSWORD_BYTES]
    return raw if raw else b" "


def _to_safe_bcrypt_str(password: str) -> str:
    """Return a string that encodes to at most 72 bytes in UTF-8. Never raises."""
    return _to_safe_bcrypt_bytes(password).decode("utf-8", errors="replace") or " "


def truncate_password_for_bcrypt(password: str) -> str:
    """Truncate password to 72 bytes (bcrypt limit). Use before hash and verify."""
    return _to_safe_bcrypt_str(password)


def hash_password(password: str) -> str:
    # Pass bytes so bcrypt never sees more than 72 bytes (avoids encoding differences)
    safe = _to_safe_bcrypt_bytes(password)
    return pwd_context.hash(safe)


def verify_password(plain: str, hashed: str) -> bool:
    safe = _to_safe_bcrypt_bytes(plain)
    return pwd_context.verify(safe, hashed)

SESSION_USER_ID_KEY = "user_id"
ROLE_SUPER_ADMIN = "SUPER_ADMIN"
ROLE_MEMBER = "MEMBER"


def get_current_user_id(request: Request) -> str | None:
    """Return user id from session or None."""
    return request.session.get(SESSION_USER_ID_KEY)


def get_current_user(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> User | None:
    """Load current user from session. Returns None if not logged in."""
    user_id_str = get_current_user_id(request)
    if not user_id_str:
        return None
    try:
        user_id = uuid.UUID(user_id_str)
        return db.query(User).filter(User.id == user_id).first()
    except (ValueError, TypeError):
        return None


def get_current_user_required(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
):
    """Load current user; redirect to login if not logged in. Returns User or RedirectResponse."""
    user = get_current_user(request, db)
    if user is None:
        return RedirectResponse(url=str(request.url_for("login_page")), status_code=302)
    return user


def require_roles(*allowed_roles: str):
    """Dependency factory: redirect if user role not in allowed_roles."""

    def dependency(
        request: Request,
        user: Annotated[User, Depends(get_current_user_required)],
    ):
        if isinstance(user, RedirectResponse):
            return user
        if user.role in allowed_roles:
            return user
        return RedirectResponse(url=str(request.url_for("index")) + "?error=forbidden", status_code=302)

    return dependency


require_super_admin = require_roles(ROLE_SUPER_ADMIN)
require_member_or_admin = require_roles(ROLE_SUPER_ADMIN, ROLE_MEMBER)
