"""
Read-only endpoint to view database tables and their structure.
"""

from sqlalchemy import inspect, text

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db, engine
from models import TruckMovement, TruckMovementCompleted, ExitBuffer

router = APIRouter(prefix="/db", tags=["Database"])


def _safe_table_count(db: Session, table_name: str):
    """Get row count for a table; works with PostgreSQL and SQLite."""
    try:
        safe_name = '"' + table_name.replace('"', '""') + '"'
        r = db.execute(text(f"SELECT COUNT(*) FROM {safe_name}"))
        return r.scalar()
    except Exception:
        return None


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
        counts[name] = _safe_table_count(db, name)
    return {"database": "postgresql" if "postgresql" in str(engine.url) else "sqlite", "counts": counts}


@router.get("/tables/data")
def get_all_tables_data(db: Session = Depends(get_db), limit: int = 100):
    """
    View data from all tables at once. Returns all rows from each table (up to limit per table).
    """
    result = {}
    
    # truck_movements
    movements = db.query(TruckMovement).limit(limit).all()
    result["truck_movements"] = [
        {
            "truck_id": r.truck_id,
            "session_id": r.session_id,
            "plate_number": r.plate_number,
            "entry_time": r.entry_time.isoformat() if r.entry_time else None,
            "axle_count": r.axle_count,
            "axle_status": r.axle_status,
            "exit_time": r.exit_time.isoformat() if r.exit_time else None,
            "status": r.status,
        }
        for r in movements
    ]
    
    # truck_movements_completed
    completed = db.query(TruckMovementCompleted).limit(limit).all()
    result["truck_movements_completed"] = [
        {
            "truck_id": r.truck_id,
            "session_id": r.session_id,
            "plate_number": r.plate_number,
            "entry_time": r.entry_time.isoformat() if r.entry_time else None,
            "axle_count": r.axle_count,
            "exit_time": r.exit_time.isoformat() if r.exit_time else None,
            "status": r.status,
        }
        for r in completed
    ]
    
    # exit_buffer
    buffer_rows = db.query(ExitBuffer).limit(limit).all()
    result["exit_buffer"] = [
        {
            "id": r.id,
            "plate_number": r.plate_number,
            "exit_time": r.exit_time.isoformat() if r.exit_time else None,
            "processed": r.processed,
            "matched_truck_id": r.matched_truck_id,
        }
        for r in buffer_rows
    ]
    
    return {
        "database": "postgresql" if "postgresql" in str(engine.url) else "sqlite",
        "data": result,
    }


@router.get("/tables/{table_name}/data")
def get_table_data(table_name: str, db: Session = Depends(get_db), limit: int = 100):
    """
    View actual data stored in a table. Returns all rows (up to limit).
    Available tables: truck_movements, truck_movements_completed, exit_buffer
    """
    if table_name == "truck_movements":
        rows = db.query(TruckMovement).limit(limit).all()
        return {
            "table": table_name,
            "count": len(rows),
            "data": [
                {
                    "truck_id": r.truck_id,
                    "session_id": r.session_id,
                    "plate_number": r.plate_number,
                    "entry_time": r.entry_time.isoformat() if r.entry_time else None,
                    "entry_image": r.entry_image,
                    "axle_count": r.axle_count,
                    "axle_processed_time": r.axle_processed_time.isoformat() if r.axle_processed_time else None,
                    "axle_status": r.axle_status,
                    "exit_time": r.exit_time.isoformat() if r.exit_time else None,
                    "exit_image": r.exit_image,
                    "status": r.status,
                }
                for r in rows
            ],
        }
    elif table_name == "truck_movements_completed":
        rows = db.query(TruckMovementCompleted).limit(limit).all()
        return {
            "table": table_name,
            "count": len(rows),
            "data": [
                {
                    "truck_id": r.truck_id,
                    "session_id": r.session_id,
                    "plate_number": r.plate_number,
                    "entry_time": r.entry_time.isoformat() if r.entry_time else None,
                    "entry_image": r.entry_image,
                    "axle_count": r.axle_count,
                    "axle_processed_time": r.axle_processed_time.isoformat() if r.axle_processed_time else None,
                    "axle_status": r.axle_status,
                    "exit_time": r.exit_time.isoformat() if r.exit_time else None,
                    "exit_image": r.exit_image,
                    "status": r.status,
                }
                for r in rows
            ],
        }
    elif table_name == "exit_buffer":
        rows = db.query(ExitBuffer).limit(limit).all()
        return {
            "table": table_name,
            "count": len(rows),
            "data": [
                {
                    "id": r.id,
                    "plate_number": r.plate_number,
                    "exit_time": r.exit_time.isoformat() if r.exit_time else None,
                    "exit_image": r.exit_image,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                    "processed": r.processed,
                    "matched_truck_id": r.matched_truck_id,
                }
                for r in rows
            ],
        }
    else:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
