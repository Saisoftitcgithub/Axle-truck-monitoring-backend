"""
SQLAlchemy ORM models for the truck monitoring system.
One table: truck_movements — one row per truck trip through the yard.
"""

from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.sql import func

from database import Base


class TruckMovement(Base):
    """
    Single row per truck trip. Tracks entry ANPR → axle detection → exit ANPR.
    """

    __tablename__ = "truck_movements"

    # Primary key: unique trip identifier
    truck_id = Column(String, primary_key=True, index=True)

    # From entry ANPR
    plate_number = Column(String, nullable=False, index=True)
    entry_time = Column(DateTime(timezone=False), nullable=False)
    entry_image = Column(String, nullable=True)

    # From axle detection stage
    axle_count = Column(Integer, nullable=True)
    axle_processed_time = Column(DateTime(timezone=False), nullable=True)
    axle_status = Column(
        String, nullable=False, default="PENDING"
    )  # PENDING | PROCESSING | DONE

    # From exit ANPR
    exit_time = Column(DateTime(timezone=False), nullable=True)
    exit_image = Column(String, nullable=True)

    # Overall trip status: IN_YARD | AXLE_DONE | EXITED
    status = Column(String, nullable=False, default="IN_YARD", index=True)

    def __repr__(self):
        return f"<TruckMovement truck_id={self.truck_id} plate={self.plate_number} status={self.status}>"
