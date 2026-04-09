from models.trip import ArchiveTrip
from core.logger import logger

def move_to_archive(db, trip):
    if trip.status == "ARCHIVED":
        return
    try:
        archive = ArchiveTrip(
            session_id=trip.session_id,
            plate_number=trip.plate_number,
            vehicle_type=trip.vehicle_type,
            event_type=trip.event_type,
            entry_time=trip.entry_time,
            entry_image=trip.entry_image,
            axle_count=trip.axle_count,
            axle_processed_time=trip.axle_processed_time,
            axle_status=trip.axle_status,
            exit_time=trip.exit_time,
            exit_image=trip.exit_image,
            status=trip.status,
            entry_sync_status=trip.entry_sync_status,
            entry_sync_time=trip.entry_sync_time,
            exit_sync_status=trip.exit_sync_status,
            exit_sync_time=trip.exit_sync_time,
            created_at=trip.created_at,
            updated_at=trip.updated_at,
        )

        db.add(archive)
        db.delete(trip)
        db.commit()

        logger.info(f"Archived successfully: {trip.session_id}")

    except Exception as e:
        db.rollback()
        logger.exception(f"Archive failed: {e}")