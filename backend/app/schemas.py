from pydantic import BaseModel
from typing import List, Optional


class Reading(BaseModel):
    sensor_type: str
    value: float
    unit: Optional[str]


class Item(BaseModel):
    device: str
    mac: Optional[str] = None
    ip: Optional[str] = None
    location: Optional[str] = None
    readings: List[Reading]
