"""
HeritageLens Database Layer
SQLAlchemy setup for SQLite (migratable to PostgreSQL).
"""
import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base

# ============================================
# DATABASE PATH
# ============================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DB_DIR, exist_ok=True)

DB_PATH = os.path.join(DB_DIR, "heritagelens.db")

# For production, use DATABASE_URL env var (PostgreSQL)
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

# ============================================
# ENGINE
# ============================================
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
    )

    # Enable foreign keys for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()
else:
    engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

# ============================================
# SESSION
# ============================================
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ============================================
# BASE
# ============================================
Base = declarative_base()


# ============================================
# DEPENDENCY (for FastAPI)
# ============================================
def get_db():
    """FastAPI dependency — yields DB session, closes after request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. Called on app startup."""
    from services.models import Monument, Language, Category, MonumentTranslation  # noqa
    Base.metadata.create_all(bind=engine)
    print(f"✅ Database initialized at {DB_PATH if DATABASE_URL.startswith('sqlite') else DATABASE_URL}")