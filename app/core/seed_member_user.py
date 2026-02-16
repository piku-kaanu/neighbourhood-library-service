"""
Create a MEMBER user linked to an existing library member.
Run: python -m app.core.seed_member_user <member_email> <password> [username]

Example:
  python -m app.core.seed_member_user john@example.com secret123
  python -m app.core.seed_member_user john@example.com secret123 john
"""
import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent.parent
if _project_root not in sys.path:
    sys.path.insert(0, str(_project_root))

from app.core.auth import hash_password
from app.database import SessionLocal
from app.models.member import Member
from app.models.user import User


def main():
    if len(sys.argv) < 3:
        print("Usage: python -m app.core.seed_member_user <member_email> <password> [username]")
        print("  member_email: email of an existing library member")
        print("  password: login password for the new user")
        print("  username: optional; defaults to member email if omitted")
        sys.exit(1)

    member_email = sys.argv[1].strip()
    password = sys.argv[2]
    username = sys.argv[3].strip() if len(sys.argv) > 3 else member_email

    if not password:
        print("Error: password cannot be empty.")
        sys.exit(1)

    db = SessionLocal()
    try:
        member = db.query(Member).filter(Member.email == member_email).first()
        if not member:
            print(f"Error: No member found with email '{member_email}'.")
            print("Create the member first via the app (Members → Add member).")
            sys.exit(1)

        existing = db.query(User).filter(User.username == username).first()
        if existing:
            print(f"Error: Username '{username}' already exists.")
            sys.exit(1)

        existing_member_user = db.query(User).filter(User.member_id == member.id).first()
        if existing_member_user:
            print(f"Error: A user is already linked to member '{member_email}' (username: {existing_member_user.username}).")
            sys.exit(1)

        user = User(
            username=username,
            password_hash=hash_password(password),
            role="MEMBER",
            member_id=member.id,
        )
        db.add(user)
        db.commit()
        print(f"MEMBER user created: username={username}, linked to member {member.full_name} ({member_email}).")
        print("They can log in and see Books and My borrows.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
