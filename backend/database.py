"""
Database configuration and session management for the truck monitoring backend.
Uses PostgreSQL when DATABASE_URL is set; falls back to SQLite for local testing when unset.
"""

import os
import uuid

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

# PostgreSQL when DATABASE_URL is set and non-empty; otherwise SQLite for local/testing
_database_url = os.environ.get("DATABASE_URL")
if _database_url and str(_database_url).strip():
    SQLALCHEMY_DATABASE_URL = _database_url.strip()
    engine_kw = {"pool_pre_ping": True, "echo": False}
else:
    # Use absolute path so same DB is used regardless of cwd
    _base = os.path.dirname(os.path.abspath(__file__))
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.join(_base, 'truck_movements.db')}"
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


def _migrate_truck_movements_session_id():
    """Add session_id to truck_movements if missing. Safe to run every startup."""
    if "sqlite" not in SQLALCHEMY_DATABASE_URL:
        return
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE truck_movements ADD COLUMN session_id VARCHAR(36)"))
            conn.commit()
    except Exception as e:
        if "duplicate column name" not in str(e).lower():
            raise
    try:
        with engine.connect() as conn:
            r = conn.execute(text("SELECT truck_id FROM truck_movements WHERE session_id IS NULL OR session_id = ''"))
            for row in r.fetchall():
                conn.execute(
                    text("UPDATE truck_movements SET session_id = :uid WHERE truck_id = :tid"),
                    {"uid": str(uuid.uuid4()), "tid": row[0]},
                )
            conn.commit()
    except Exception:
        pass


def init_db():
    """Create all tables and run migrations. Called on application startup."""
    Base.metadata.create_all(bind=engine)
    _migrate_truck_movements_session_id()
