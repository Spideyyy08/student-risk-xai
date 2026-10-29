"""
Database Schema Initialization Script.
Creates all application tables using SQLAlchemy 2.0 Base metadata.
Windows-safe bootstrap, plain ASCII logging.
"""

import sys
from pathlib import Path

# Bootstrap sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db.base import Base
from app.db.session import engine
import app.models  # Ensure all models are imported into metadata


def create_all_tables():
    print("Connecting to database...")
    print(f"Engine URL dialect: {engine.dialect.name}")
    print("Creating database schema tables...")

    Base.metadata.create_all(bind=engine)

    print("\nDatabase tables initialized successfully:")
    for table_name in sorted(Base.metadata.tables.keys()):
        print(f"  [OK] {table_name}")

    print("\nTable creation complete.")


if __name__ == "__main__":
    create_all_tables()
