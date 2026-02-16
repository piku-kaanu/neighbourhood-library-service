"""Create a super admin user if none exist. Run: python -m app.core.seed_admin"""
import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent.parent
if _project_root not in sys.path:
    sys.path.insert(0, str(_project_root))

from app.core.auth import hash_password
from app.database import SessionLocal
from app.models.user import User


def main():
    db = SessionLocal()
    try:
        if db.query(User).first():
            print("A user already exists. Skipping seed.")
            return
        admin = User(
            username="admin",
            password_hash=hash_password("admin"),
            role="SUPER_ADMIN",
            member_id=None,
        )
        db.add(admin)
        db.commit()
        print("Super admin created: username=admin, password=admin. Change the password after first login.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
