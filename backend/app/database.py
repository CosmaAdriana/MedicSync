"""
MedicSync — Database Configuration
SQLAlchemy engine, session factory, and declarative base for SQLite (dev).
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# ---------------------------------------------------------------------------
# Database URL — SQLite for local development, swap to PostgreSQL in prod
# ---------------------------------------------------------------------------
SQLALCHEMY_DATABASE_URL = "sqlite:///./medicsync.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # required for SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# ---------------------------------------------------------------------------
# FastAPI dependency — yields a DB session per request
# ---------------------------------------------------------------------------
def get_db():
    """Dependency that provides a SQLAlchemy session and closes it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
