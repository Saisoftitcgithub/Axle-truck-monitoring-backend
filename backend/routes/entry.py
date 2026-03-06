"""
Entry ANPR routes: create a new truck movement and trigger axle detection.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from database import get_db
from models import TruckMovement
from schemas import EntryANPRRequest
from axle_runner import run_axle_detection

router = APIRouter(prefix="/entry-anpr", tags=["Entry ANPR"])


@router.get("", status_code=200)
def get_entry_anpr_help():
    """
    This endpoint expects POST with JSON body. Use the docs or send POST with:
    truck_id, plate_number, entry_time (ISO), image_path.
    """
    return {
        "message": "Use POST to register truck entry",
        "method": "POST",
        "body": {
            "truck_id": "string (e.g. TRK001)",
            "plate_number": "string (e.g. TN01AB1234)",
            "entry_time": "ISO datetime (e.g. 2026-02-03T10:15:22)",
            "image_path": "string (e.g. images/entry.jpg)",
        },
        "docs": "/docs",
        "example_curl": 'curl -X POST "http://127.0.0.1:8002/entry-anpr" -H "Content-Type: application/json" -d "{\\"truck_id\\":\\"TRK001\\",\\"plate_number\\":\\"TN01AB1234\\",\\"entry_time\\":\\"2026-02-03T10:15:22\\",\\"image_path\\":\\"images/entry.jpg\\"}"',
    }


@router.post("", status_code=201)
def post_entry_anpr(
    body: EntryANPRRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Register truck entry from ANPR camera.
    Inserts a new row in truck_movements with status=IN_YARD, axle_status=PENDING,
    then starts a background task to run axle detection for this truck_id.
    """
    try:
        return _do_post_entry_anpr(body, background_tasks, db)
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal Server Error",
                "error": str(e),
                "type": type(e).__name__,
                "traceback": traceback.format_exc(),
            },
        )


def _do_post_entry_anpr(body: EntryANPRRequest, background_tasks: BackgroundTasks, db: Session):
    """Actual entry logic so we can wrap in try/except in route."""
    existing = db.query(TruckMovement).filter(TruckMovement.truck_id == body.truck_id).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"truck_id '{body.truck_id}' already exists")

    # Server-generated session id for the trip
    session_id = str(uuid.uuid4())

    # Parse entry_time (ISO string) — store as datetime
    try:
        entry_dt = datetime.fromisoformat(body.entry_time.replace("Z", "+00:00"))
        # SQLite doesn't store timezone; use naive UTC if needed
        if entry_dt.tzinfo:
            entry_dt = entry_dt.replace(tzinfo=None)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid entry_time format; use ISO datetime")

    movement = TruckMovement(
        truck_id=body.truck_id,
        session_id=session_id,
        plate_number=body.plate_number,
        entry_time=entry_dt,
        entry_image=body.image_path,
        axle_status="PENDING",
        status="IN_YARD",
    )
    db.add(movement)
    db.commit()
    db.refresh(movement)

    # Run axle detection in background after response is sent (no Celery/Redis)
    background_tasks.add_task(run_axle_detection, body.truck_id)

    return {
        "message": "Entry recorded",
        "truck_id": movement.truck_id,
        "session_id": movement.session_id,
        "status": movement.status,
        "axle_status": movement.axle_status,
    }
