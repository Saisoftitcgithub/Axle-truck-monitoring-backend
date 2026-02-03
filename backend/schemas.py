"""
Pydantic schemas for request/response validation in the truck monitoring API.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ----- Entry ANPR -----


class EntryANPRRequest(BaseModel):
    """Request body for POST /entry-anpr."""

    truck_id: str = Field(..., description="Unique trip identifier")
    plate_number: str = Field(..., description="License plate from entry camera")
    entry_time: str = Field(..., description="ISO datetime e.g. 2026-02-03T10:15:22")
    image_path: str = Field(..., description="Path to entry ANPR image")

    class Config:
        json_schema_extra = {
            "example": {
                "truck_id": "TRK123",
                "plate_number": "TN01AB1234",
                "entry_time": "2026-02-03T10:15:22",
                "image_path": "images/entry.jpg",
            }
        }


# ----- Axle status update (internal / update-axle-status) -----


class UpdateAxleStatusRequest(BaseModel):
    """Request body for POST /update-axle-status."""

    truck_id: str
    axle_status: str = Field(..., description="PENDING | PROCESSING | DONE")


# ----- Axle detection result -----


class AxleDetectionRequest(BaseModel):
    """Request body for POST /axle-detection."""

    truck_id: str
    axle_count: int = Field(..., ge=0, description="Detected number of axles")
    processed_time: str = Field(
        ..., description="ISO datetime when processing finished (UTC)"
    )


# ----- Exit ANPR -----


class ExitANPRRequest(BaseModel):
    """Request body for POST /exit-anpr."""

    plate_number: str = Field(..., description="License plate from exit camera")
    exit_time: str = Field(..., description="ISO datetime e.g. 2026-02-03T10:25:03")
    image_path: str = Field(..., description="Path to exit ANPR image")

    class Config:
        json_schema_extra = {
            "example": {
                "plate_number": "TN01AB1234",
                "exit_time": "2026-02-03T10:25:03",
                "image_path": "images/exit.jpg",
            }
        }


# ----- Optional: response schemas -----


class TruckMovementResponse(BaseModel):
    """Full truck movement record (for responses if needed)."""

    truck_id: str
    plate_number: str
    entry_time: datetime
    entry_image: Optional[str] = None
    axle_count: Optional[int] = None
    axle_processed_time: Optional[datetime] = None
    axle_status: str
    exit_time: Optional[datetime] = None
    exit_image: Optional[str] = None
    status: str

    class Config:
        from_attributes = True
