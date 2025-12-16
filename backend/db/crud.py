from typing import List, Optional
from sqlalchemy.orm import Session
from . import models, schemas


def create_event(db: Session, data: schemas.EventCreateInternal) -> models.Event:
    event = models.Event(
        object_id=data.object_id,
        owner_id=data.owner_id,
        bbox=data.bbox,
        frame_snapshot_path=data.frame_snapshot_path,
        event_timestamp=data.timestamp,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def get_event(db: Session, event_id: int) -> Optional[models.Event]:
    return db.query(models.Event).filter(models.Event.id == event_id).first()


def list_events(
    db: Session,
    status: Optional[models.EventStatus],
    limit: int,
    offset: int,
) -> List[models.Event]:
    q = db.query(models.Event)
    if status is not None:
        q = q.filter(models.Event.status == status)
    return (
        q.order_by(models.Event.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

def update_event_status(
    db: Session,
    event_id: int,
    new_status: models.EventStatus,
) -> models.Event | None:
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if event is None:
        return None
    event.status = new_status
    db.commit()
    db.refresh(event)
    return event