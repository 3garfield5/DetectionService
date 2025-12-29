import enum
from sqlalchemy import (
    Column, Integer, Float,
    Enum, Text, TIMESTAMP, func
)
from sqlalchemy.dialects.postgresql import JSONB
from .base import Base


class EventStatus(str, enum.Enum):
    new = "new"
    confirmed = "confirmed"
    dismissed = "dismissed"


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)

    object_id = Column(Integer, nullable=True)
    owner_id = Column(Integer, nullable=True)

    bbox = Column(JSONB, nullable=True)

    frame_snapshot_path = Column(Text, nullable=False)

    status = Column(Enum(EventStatus), nullable=False, default=EventStatus.new)

    event_timestamp = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
    )

    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
