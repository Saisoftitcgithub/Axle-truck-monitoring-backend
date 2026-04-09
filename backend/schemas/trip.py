from pydantic import BaseModel


class EntryRequest(BaseModel):
    plate_number: str
    vehicle_type: str
    entry_time: str
    image_path: str

class ExitRequest(BaseModel):
    plate_number: str
    exit_time: str
    image_path: str