"""
SQLAlchemy ORM models for the truck monitoring system.
truck_movements = active/pending trips; truck_movements_completed = exited trips;
exit_buffer = staging for exit ANPR events before matching.
"""

from datetime import datetime

from sqlalchemy import Column, String, Integer, DateTime, Boolean

from database import Base


class TruckMovement(Base):
    """
    Active/pending trips. One row per truck trip: entry → axle → exit.
    status: IN_YARD | AXLE_DONE | EXITED. EXITED rows are moved to
    truck_movements_completed by the hourly job.
    """

    __tablename__ = "truck_movements"

    truck_id = Column(String, primary_key=True, index=True)
    session_id = Column(String(36), unique=True, nullable=False, index=True)
    plate_number = Column(String, nullable=False, index=True)
    entry_time = Column(DateTime(timezone=False), nullable=False)
    entry_image = Column(String, nullable=True)
    axle_count = Column(Integer, nullable=True)
    axle_processed_time = Column(DateTime(timezone=False), nullable=True)
    axle_status = Column(String, nullable=False, default="PENDING")
    exit_time = Column(DateTime(timezone=False), nullable=True)
    exit_image = Column(String, nullable=True)
    status = Column(String, nullable=False, default="IN_YARD", index=True)

    def __repr__(self):
        return f"<TruckMovement truck_id={self.truck_id} session_id={self.session_id} status={self.status}>"


class TruckMovementCompleted(Base):
    """
    Completed trips (exited). Hourly job moves EXITED rows from
    truck_movements here. Same schema as TruckMovement.
    """

    __tablename__ = "truck_movements_completed"

    truck_id = Column(String, primary_key=True, index=True)
    session_id = Column(String(36), nullable=False, index=True)
    plate_number = Column(String, nullable=False, index=True)
    entry_time = Column(DateTime(timezone=False), nullable=False)
    entry_image = Column(String, nullable=True)
    axle_count = Column(Integer, nullable=True)
    axle_processed_time = Column(DateTime(timezone=False), nullable=True)
    axle_status = Column(String, nullable=False, default="PENDING")
    exit_time = Column(DateTime(timezone=False), nullable=True)
    exit_image = Column(String, nullable=True)
    status = Column(String, nullable=False, default="EXITED", index=True)

    def __repr__(self):
        return f"<TruckMovementCompleted truck_id={self.truck_id} session_id={self.session_id}>"


class ExitBuffer(Base):
    """
    Buffer for exit ANPR events. Every exit request is written here first,
    then matched to a truck and applied. processed=True when matched.
    """

    __tablename__ = "exit_buffer"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plate_number = Column(String, nullable=False, index=True)
    exit_time = Column(DateTime(timezone=False), nullable=False)
    exit_image = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=False), nullable=False, default=datetime.utcnow)
    processed = Column(Boolean, nullable=False, default=False, index=True)
    matched_truck_id = Column(String, nullable=True, index=True)
