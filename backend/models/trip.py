from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from db.base import Base

class ActiveTrip(Base):
    __tablename__ = "active_trips"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)

    plate_number = Column(String, index=True)
    vehicle_type = Column(String)

    event_type = Column(String)  # ENTRY/EXIT

    entry_time = Column(DateTime)
    entry_image = Column(Text)

    axle_count = Column(Integer, default=0)
    axle_processed_time = Column(DateTime)
    axle_status = Column(String, default="PENDING")

    exit_time = Column(DateTime)
    exit_image = Column(Text)

    status = Column(String, default="IN_YARD")
    
    entry_sync_status = Column(String, default="PENDING")
    entry_sync_time = Column(DateTime)

    exit_sync_status = Column(String, default="PENDING")
    exit_sync_time = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ArchiveTrip(Base):
    __tablename__ = "archive_trips"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)

    plate_number = Column(String, index=True)
    vehicle_type = Column(String)

    event_type = Column(String)

    entry_time = Column(DateTime)
    entry_image = Column(Text)

    axle_count = Column(Integer)
    axle_processed_time = Column(DateTime)
    axle_status = Column(String)

    exit_time = Column(DateTime)
    exit_image = Column(Text)

    status = Column(String)

    entry_sync_status = Column(String)
    entry_sync_time = Column(DateTime)

    exit_sync_status = Column(String)
    exit_sync_time = Column(DateTime)

    created_at = Column(DateTime)
    updated_at = Column(DateTime)