"""Create all database tables from SQLAlchemy models.
Run from project root:  python -m app.core.create_tables
Or from anywhere:       python path/to/app/core/create_tables.py
"""
import sys
from pathlib import Path

# Ensure project root is on path when script is run directly
_project_root = Path(__file__).resolve().parent.parent.parent
if _project_root not in sys.path:
    sys.path.insert(0, str(_project_root))

from app.database import engine
from app.models import Base

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("Tables created.")
