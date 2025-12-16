from typing import Optional, Literal, List
from datetime import datetime
from pydantic import BaseModel

EventStatusLiteral = Literal["new", "confirmed", "dismissed"]

class EventStatusUpdate(BaseModel):
    status: EventStatusLiteral

class EventCreateInternal(BaseModel):
    timestamp: datetime
    owner_id: Optional[int] = None
    object_id: Optional[int] = None
    bbox: List[float]
    frame_snapshot_base64: Optional[str] = None
    frame_snapshot_path: Optional[str] = None

class EventOut(BaseModel):
    id: int
    object_id: Optional[int]
    owner_id: Optional[int]
    bbox: Optional[List[float]]
    frame_snapshot_url: str
    status: EventStatusLiteral
    event_timestamp: datetime
    created_at: datetime
    updated_at: datetime
