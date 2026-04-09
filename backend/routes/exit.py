from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from dependencies.db import get_db
from models.trip import ActiveTrip
from schemas.trip import ExitRequest
from services.sync_service import sync_to_ajman
from services.archive_service import move_to_archive
from core.logger import logger

router = APIRouter(prefix="/exit", tags=["Exit"])


@router.post("/")
async def exit_event(body: ExitRequest, db: Session = Depends(get_db)):
    try:
        trip = (
            db.query(ActiveTrip)
            .filter(
                ActiveTrip.plate_number == body.plate_number,
                ActiveTrip.exit_time == None   
            )
            .order_by(ActiveTrip.entry_time.desc())
            .first()
        )

        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")

        trip.exit_time = datetime.fromisoformat(body.exit_time)
        trip.exit_image = body.image_path
        trip.event_type = "EXIT"
        trip.status = "COMPLETED"

        sync = await sync_to_ajman(trip)

        trip.exit_sync_status = sync["status"]
        trip.exit_sync_time = sync["time"]

        db.commit()

        # archive conditn
        if (
            trip.entry_sync_status == "SUCCESS"
            and trip.exit_sync_status == "SUCCESS"
            and trip.axle_status == "DONE"
        ):
            if trip.status != "ARCHIVED":  
                move_to_archive(db, trip)
                logger.info(f"Archived from exit: {trip.session_id}")
        else:
            logger.info(
                f"Archive skipped: {trip.session_id} | "
                f"entry={trip.entry_sync_status}, "
                f"exit={trip.exit_sync_status}, "
                f"axle={trip.axle_status}"
            )

        logger.info(f"Exit processed: {trip.session_id}")

        return {"message": "Exit successful"}

    except HTTPException:
        raise

    except Exception as e:
        db.rollback()  
        logger.exception(f"Exit failed: {e}")
        raise HTTPException(status_code=500, detail="Exit failed")