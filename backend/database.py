"""
Database configuration and session management for the truck monitoring backend.
Uses PostgreSQL when DATABASE_URL is set; falls back to SQLite for local testing when unset.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

# PostgreSQL when DATABASE_URL is set and non-empty; otherwise SQLite for local/testing
_database_url = os.environ.get("DATABASE_URL")
if _database_url and str(_database_url).strip():
    SQLALCHEMY_DATABASE_URL = _database_url.strip()
    engine_kw = {"pool_pre_ping": True, "echo": False}
else:
    SQLALCHEMY_DATABASE_URL = "sqlite:///./truck_movements.db"
    engine_kw = {
        "connect_args": {"check_same_thread": False},
        "poolclass": StaticPool,
        "echo": False,
    }

engine = create_engine(SQLALCHEMY_DATABASE_URL, **engine_kw)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """
    Dependency that yields a DB session. Used with FastAPI's Depends().
    Ensures the session is closed after the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Create all tables in the database. Called on application startup.
    """
    Base.metadata.create_all(bind=engine)
