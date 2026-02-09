"""
Hourly job: move EXITED rows from truck_movements to truck_movements_completed,
and process any unprocessed exit_buffer rows.
"""

from database import SessionLocal
from models import TruckMovement, TruckMovementCompleted, ExitBuffer


def run_hourly_job() -> None:
    db = SessionLocal()
    try:
        # 1. Move EXITED rows to truck_movements_completed
        exited = db.query(TruckMovement).filter(TruckMovement.status == "EXITED").all()
        for m in exited:
            completed = TruckMovementCompleted(
                truck_id=m.truck_id,
                session_id=m.session_id,
                plate_number=m.plate_number,
                entry_time=m.entry_time,
                entry_image=m.entry_image,
                axle_count=m.axle_count,
                axle_processed_time=m.axle_processed_time,
                axle_status=m.axle_status,
                exit_time=m.exit_time,
                exit_image=m.exit_image,
                status="EXITED",
            )
            db.add(completed)
            db.delete(m)
        db.commit()

        # 2. Process unprocessed exit buffer rows
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
    finally:
        db.close()
