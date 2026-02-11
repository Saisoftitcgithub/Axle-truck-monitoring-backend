"""
Read-only endpoint to view database tables and their structure.
"""

from sqlalchemy import inspect, text

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db, engine

router = APIRouter(prefix="/db", tags=["Database"])


@router.get("/tables")
def get_tables():
    """
    List all tables and their columns. Use this to see the database structure.
    Works with both PostgreSQL and SQLite.
    """
    insp = inspect(engine)
    table_names = insp.get_table_names()
    result = []
    for name in table_names:
        columns = insp.get_columns(name)
        result.append({
            "table": name,
            "columns": [
                {"name": c["name"], "type": str(c["type"])}
                for c in columns
            ],
        })
    return {"database": "postgresql" if "postgresql" in str(engine.url) else "sqlite", "tables": result}


@router.get("/tables/counts")
def get_table_counts(db: Session = Depends(get_db)):
    """
    List each table with its row count. Helps you see how much data is stored.
    """
    insp = inspect(engine)
    table_names = insp.get_table_names()
    counts = {}
    for name in table_names:
        try:
            r = db.execute(text("SELECT COUNT(*) FROM " + name.replace('"', '""')))
            counts[name] = r.scalar()
        except Exception:
            counts[name] = None
    return {"database": "postgresql" if "postgresql" in str(engine.url) else "sqlite", "counts": counts}
