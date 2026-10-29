"""
CLI Script to create or update an administrator account.
"""

import sys
import argparse
from pathlib import Path

# Bootstrap sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import hash_password


def main():
    parser = argparse.ArgumentParser(description="Create administrator user.")
    parser.add_argument("--username", default="admin")
    parser.add_argument("--password", default="admin123")
    parser.add_argument("--name", default="Head of Department (Admin)")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.username == args.username))
        if user:
            user.password_hash = hash_password(args.password)
            user.full_name = args.name
            user.role = "ADMIN"
            user.is_active = True
            print(f"[OK] Updated existing admin user '{args.username}'.")
        else:
            new_u = User(
                username=args.username,
                password_hash=hash_password(args.password),
                full_name=args.name,
                role="ADMIN",
                department="Computer Engineering",
                is_active=True,
            )
            db.add(new_u)
            print(f"[OK] Created new admin user '{args.username}'.")
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
