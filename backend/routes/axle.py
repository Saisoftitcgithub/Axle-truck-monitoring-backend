"""
Axle detection routes: update axle status and record axle count + processed time.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import TruckMovement
from schemas import UpdateAxleStatusRequest, AxleDetectionRequest

router = APIRouter(tags=["Axle"])


@router.post("/update-axle-status", include_in_schema=False)
def post_update_axle_status(
    body: UpdateAxleStatusRequest,
    db: Session = Depends(get_db),
):
    """
    Update axle_status for a truck (e.g. PROCESSING when axle script starts).
    """
    movement = db.query(TruckMovement).filter(TruckMovement.truck_id == body.truck_id).first()
    if not movement:
        raise HTTPException(status_code=404, detail=f"truck_id '{body.truck_id}' not found")

    movement.axle_status = body.axle_status
    db.commit()
    return {"message": "axle_status updated", "truck_id": body.truck_id, "axle_status": body.axle_status}


@router.post("/axle-detection", include_in_schema=False)
def post_axle_detection(
    body: AxleDetectionRequest,
    db: Session = Depends(get_db),
):
    """
    Record axle detection result: axle_count, axle_processed_time,
    set axle_status=DONE and status=AXLE_DONE.
    """
    movement = db.query(TruckMovement).filter(TruckMovement.truck_id == body.truck_id).first()
    if not movement:
        raise HTTPException(status_code=404, detail=f"truck_id '{body.truck_id}' not found")

    from datetime import datetime
    try:
        processed_dt = datetime.fromisoformat(body.processed_time.replace("Z", "+00:00"))
        if processed_dt.tzinfo:
            processed_dt = processed_dt.replace(tzinfo=None)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid processed_time format; use ISO datetime")

    movement.axle_count = body.axle_count
    movement.axle_processed_time = processed_dt
    movement.axle_status = "DONE"
    movement.status = "AXLE_DONE"
    db.commit()
    return {
        "message": "Axle detection recorded",
        "truck_id": body.truck_id,
        "axle_count": body.axle_count,
        "status": movement.status,
    }
