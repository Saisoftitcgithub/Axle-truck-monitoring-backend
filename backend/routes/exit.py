"""
Exit ANPR routes: buffer exit events then match to truck and update.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import TruckMovement, ExitBuffer

from schemas import ExitANPRRequest

router = APIRouter(prefix="/exit-anpr", tags=["Exit ANPR"])


@router.get("", status_code=200)
def get_exit_anpr_help():
    """This endpoint expects POST with JSON body. Use POST with plate_number, exit_time, image_path."""
    return {
        "message": "Use POST to register truck exit",
        "method": "POST",
        "body": {
            "plate_number": "string",
            "exit_time": "ISO datetime (e.g. 2026-02-03T10:25:03)",
            "image_path": "string",
        },
        "docs": "/docs",
    }


def _parse_exit_time(exit_time_str: str) -> datetime:
    dt = datetime.fromisoformat(exit_time_str.replace("Z", "+00:00"))
    if dt.tzinfo:
        dt = dt.replace(tzinfo=None)
    return dt


def _process_exit_buffer(db: Session) -> None:
    """
    Process all unprocessed exit buffer rows: match by plate_number to
    latest non-exited truck, update movement, mark buffer row processed.
    """
    unprocessed = db.query(ExitBuffer).filter(ExitBuffer.processed == False).order_by(ExitBuffer.created_at).all()
    for row in unprocessed:
        movement = (
            db.query(TruckMovement)
            .filter(
                TruckMovement.plate_number == row.plate_number,
                TruckMovement.status != "EXITED",
            )
            .order_by(TruckMovement.entry_time.desc())
            .first()
        )
        if movement:
            movement.exit_time = row.exit_time
            movement.exit_image = row.exit_image
            movement.status = "EXITED"
            row.processed = True
            row.matched_truck_id = movement.truck_id
    db.commit()


@router.post("", status_code=200)
def post_exit_anpr(
    body: ExitANPRRequest,
    db: Session = Depends(get_db),
):
    """
    Register truck exit from ANPR camera.
    Writes to exit_buffer first, then processes buffer (match by plate,
    update truck_movements, mark buffer processed).
    """
    try:
        exit_dt = _parse_exit_time(body.exit_time)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid exit_time format; use ISO datetime")

    # 1. Buffer: store exit event
    buffer_row = ExitBuffer(
        plate_number=body.plate_number,
        exit_time=exit_dt,
        exit_image=body.image_path,
        processed=False,
    )
    db.add(buffer_row)
    db.commit()
    db.refresh(buffer_row)

    # 2. Process buffer (this row and any other unprocessed)
    _process_exit_buffer(db)

    # 3. Find the movement we just updated (for response)
    movement = (
        db.query(TruckMovement)
        .filter(
            TruckMovement.plate_number == body.plate_number,
            TruckMovement.status == "EXITED",
            TruckMovement.exit_time == exit_dt,
        )
        .order_by(TruckMovement.entry_time.desc())
        .first()
    )
    if not movement:
        # Buffer was applied but match might be on a different exit_time; use latest exited for this plate
        movement = (
            db.query(TruckMovement)
            .filter(TruckMovement.plate_number == body.plate_number, TruckMovement.status == "EXITED")
            .order_by(TruckMovement.exit_time.desc())
            .first()
        )
    if not movement:
        return {
            "message": "Exit event buffered; no matching non-exited truck found",
            "plate_number": body.plate_number,
            "buffered": True,
        }

    return {
        "message": "Exit recorded",
        "truck_id": movement.truck_id,
        "session_id": movement.session_id,
        "plate_number": movement.plate_number,
        "status": movement.status,
    }
