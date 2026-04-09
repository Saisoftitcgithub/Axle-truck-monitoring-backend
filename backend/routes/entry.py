import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from core.logger import logger
from dependencies.db import get_db
from models.trip import ActiveTrip
from schemas.trip import EntryRequest
from services.axle_service import run_axle_detection


router = APIRouter(prefix="/entry", tags=["Entry"])

@router.post("/")
async def create_entry(
    body: EntryRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    try:
        existing_trip = (
            db.query(ActiveTrip)
            .filter(
                ActiveTrip.plate_number == body.plate_number,
                ActiveTrip.exit_time == None  
            )
            .first()
        )

        if existing_trip:
            logger.info(f"Duplicate entry blocked: {body.plate_number}")
            return {
                "message": "Truck already inside",
                "session_id": existing_trip.session_id
            }
        session_id = str(uuid.uuid4())

        trip = ActiveTrip(
            session_id=session_id,
            plate_number=body.plate_number,
            vehicle_type=body.vehicle_type,
            event_type="ENTRY",
            entry_time=datetime.fromisoformat(body.entry_time),
            entry_image=body.image_path
        )

        db.add(trip)
        db.commit()

        logger.info(f"Entry created: {session_id}")

        background_tasks.add_task(run_axle_detection, session_id)

        return {
            "message": "Entry successful",
            "session_id": session_id
        }

    except Exception as e:
        db.rollback()  
        logger.exception(f"Entry failed: {e}")
        raise HTTPException(status_code=500, detail="Entry failed")