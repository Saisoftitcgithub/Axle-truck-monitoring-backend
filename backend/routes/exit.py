"""
Exit ANPR routes: match by plate_number and mark truck as exited.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import TruckMovement

from schemas import ExitANPRRequest

router = APIRouter(prefix="/exit-anpr", tags=["Exit ANPR"])


@router.post("", status_code=200)
def post_exit_anpr(
    body: ExitANPRRequest,
    db: Session = Depends(get_db),
):
    """
    Register truck exit from ANPR camera.
    Finds the latest record with matching plate_number where status != 'EXITED',
    then updates exit_time, exit_image, and status='EXITED'.
    """
    # Latest record for this plate that has not yet exited
    movement = (
        db.query(TruckMovement)
        .filter(
            TruckMovement.plate_number == body.plate_number,
            TruckMovement.status != "EXITED",
        )
        .order_by(TruckMovement.entry_time.desc())
        .first()
    )
    if not movement:
        raise HTTPException(
            status_code=404,
            detail=f"No non-exited record found for plate_number '{body.plate_number}'",
        )

    from datetime import datetime
    try:
        exit_dt = datetime.fromisoformat(body.exit_time.replace("Z", "+00:00"))
        if exit_dt.tzinfo:
            exit_dt = exit_dt.replace(tzinfo=None)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid exit_time format; use ISO datetime")

    movement.exit_time = exit_dt
    movement.exit_image = body.image_path
    movement.status = "EXITED"
    db.commit()
    db.refresh(movement)

    return {
        "message": "Exit recorded",
        "truck_id": movement.truck_id,
        "plate_number": movement.plate_number,
        "status": movement.status,
    }
