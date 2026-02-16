# app/api/members.py

import re
import uuid
from datetime import date
from pathlib import Path
from typing import Optional

from fastapi import Depends, APIRouter, Form, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.member import Member

router = APIRouter(prefix="/api/v1/members", tags=["members"])

templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")

# Email: basic format (local@domain with at least one dot in domain)
EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
# Phone: digits, optional + at start, optional spaces/dashes/parens; 10–20 digit chars
PHONE_RE = re.compile(r"^\+?[\d\s\-()]{10,20}$")


def validate_email(s: str) -> Optional[str]:
    """Return error message if invalid, else None."""
    if not s or not s.strip():
        return "Email is required."
    if len(s.strip()) > 255:
        return "Email is too long."
    if not EMAIL_RE.match(s.strip()):
        return "Enter a valid email address (e.g. name@example.com)."
    return None


def validate_phone(s: str) -> Optional[str]:
    """Return error message if invalid, else None."""
    if not s or not s.strip():
        return "Phone is required."
    cleaned = re.sub(r"[\s\-()]", "", s.strip())
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]
    if not cleaned.isdigit():
        return "Phone must contain only digits, spaces, dashes, or parentheses."
    if len(cleaned) < 10 or len(cleaned) > 15:
        return "Phone must be 10–15 digits."
    if len(s.strip()) > 20:
        return "Phone is too long."
    return None


def filter_members_query(
    db: Session,
    name: Optional[str],
    email: Optional[str],
    is_active: Optional[str],
):
    """Build filtered query. is_active: 'true' = active only, 'false' = inactive only, else all."""
    q = db.query(Member)
    if name and name.strip():
        q = q.filter(Member.full_name.ilike(f"%{name.strip()}%"))
    if email and email.strip():
        q = q.filter(Member.email.ilike(f"%{email.strip()}%"))
    if is_active == "true" or is_active == "yes":
        q = q.filter(Member.is_active == True)
    elif is_active == "false" or is_active == "no":
        q = q.filter(Member.is_active == False)
    return q.order_by(Member.full_name)


@router.get("/", response_class=HTMLResponse)
def members_list(
    request: Request,
    db: Session = Depends(get_db),
    name: Optional[str] = Query(None),
    email: Optional[str] = Query(None),
    is_active: Optional[str] = Query(None),
):
    """List all members (HTML page) with optional filters."""
    members = filter_members_query(db, name, email, is_active).all()
    return templates.TemplateResponse(
        request=request,
        name="members_list.html",
        context={
            "members": members,
            "filter_name": name or "",
            "filter_email": email or "",
            "filter_is_active": is_active or "all",
        },
    )


@router.get("/new", response_class=HTMLResponse)
def member_new(request: Request):
    """Show add-member form."""
    return templates.TemplateResponse(
        request=request,
        name="member_form.html",
        context={"errors": None},
    )


@router.post("/")
def member_create(
    request: Request,
    db: Session = Depends(get_db),
    full_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    membership_date: str = Form(...),
    is_active: str = Form("true"),
):
    """Create a member from form."""
    errors = {}
    if not full_name or not full_name.strip():
        errors["full_name"] = "Full name is required."
    email_err = validate_email(email)
    if email_err:
        errors["email"] = email_err
    phone_err = validate_phone(phone)
    if phone_err:
        errors["phone"] = phone_err
    if not membership_date or not membership_date.strip():
        errors["membership_date"] = "Membership date is required."
    try:
        parsed_date = date.fromisoformat(membership_date.strip())
    except ValueError:
        errors["membership_date"] = "Invalid date (use YYYY-MM-DD)."
        parsed_date = None

    if not errors:
        existing = db.query(Member).filter(Member.email == email.strip()).first()
        if existing:
            errors["email"] = "A member with this email already exists."

    if errors:
        return templates.TemplateResponse(
            request=request,
            name="member_form.html",
            context={
                "errors": errors,
                "full_name": full_name.strip() if full_name else "",
                "email": email.strip() if email else "",
                "phone": (phone or "").strip(),
                "membership_date": membership_date.strip() if membership_date else "",
                "is_active": is_active,
            },
            status_code=422,
        )

    member = Member(
        full_name=full_name.strip(),
        email=email.strip(),
        phone=phone.strip(),
        membership_date=parsed_date,
        is_active=is_active.lower() in ("true", "yes", "1"),
    )
    db.add(member)
    db.commit()
    return RedirectResponse(url=request.url_for("members_list"), status_code=303)


@router.put("/{member_id}")
def member_update(
    member_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    full_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    membership_date: str = Form(...),
    is_active: str = Form("true"),
):
    """Update a member. Returns JSON for inline save."""
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        return JSONResponse(status_code=404, content={"error": "Member not found"})

    errors = {}
    if not full_name or not full_name.strip():
        errors["full_name"] = "Full name is required."
    email_err = validate_email(email)
    if email_err:
        errors["email"] = email_err
    phone_err = validate_phone(phone)
    if phone_err:
        errors["phone"] = phone_err
    if not membership_date or not membership_date.strip():
        errors["membership_date"] = "Membership date is required."
    try:
        parsed_date = date.fromisoformat(membership_date.strip())
    except ValueError:
        errors["membership_date"] = "Invalid date (use YYYY-MM-DD)."
        parsed_date = None

    if not errors:
        existing = db.query(Member).filter(Member.email == email.strip(), Member.id != member_id).first()
        if existing:
            errors["email"] = "A member with this email already exists."

    if errors:
        return JSONResponse(status_code=422, content={"errors": errors})

    member.full_name = full_name.strip()
    member.email = email.strip()
    member.phone = phone.strip()
    member.membership_date = parsed_date
    member.is_active = is_active.lower() in ("true", "yes", "1")
    db.commit()
    db.refresh(member)
    return JSONResponse(
        status_code=200,
        content={
            "id": str(member.id),
            "full_name": member.full_name,
            "email": member.email,
            "phone": member.phone,
            "membership_date": member.membership_date.isoformat(),
            "is_active": member.is_active,
        },
    )


@router.delete("/{member_id}")
def member_delete(member_id: uuid.UUID, db: Session = Depends(get_db)):
    """Delete a member."""
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        return JSONResponse(status_code=404, content={"error": "Member not found"})
    db.delete(member)
    db.commit()
    return JSONResponse(status_code=200, content={"ok": True})
