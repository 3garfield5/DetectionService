# app/api/events.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from db import crud, schemas, models
from db.base import get_db

router = APIRouter(prefix="/events", tags=["events"])

SNAPSHOT_BASE_URL = "http://127.0.0.1:8000/snapshots/"

def build_snapshot_url(path: str) -> str:
    return SNAPSHOT_BASE_URL.rstrip("/") + "/" + path.lstrip("/")


def to_event_out(e) -> schemas.EventOut:
    return schemas.EventOut(
        id=e.id,
        object_id=e.object_id,
        owner_id=e.owner_id,
        bbox=e.bbox,
        frame_snapshot_url=build_snapshot_url(e.frame_snapshot_path),
        status=e.status.value,
        event_timestamp=e.event_timestamp,
        created_at=e.created_at,
        updated_at=e.updated_at,
    )

@router.get("/", response_model=List[schemas.EventOut])
def get_events(
    status: Optional[schemas.EventStatusLiteral] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    event_status = models.EventStatus(status) if status else None
    events = crud.list_events(db, event_status, limit, offset)

    result: List[schemas.EventOut] = []
    for e in events:
        result.append(
            schemas.EventOut(
                id=e.id,
                object_id=e.object_id,
                owner_id=e.owner_id,
                bbox=e.bbox,
                frame_snapshot_url=build_snapshot_url(e.frame_snapshot_path),
                status=e.status.value,
                event_timestamp=e.event_timestamp,
                created_at=e.created_at,
                updated_at=e.updated_at,
            )
        )
    return result


@router.get("/{event_id}", response_model=schemas.EventOut)
def get_event(
    event_id: int,
    db: Session = Depends(get_db),
):
    e = crud.get_event(db, event_id)
    if e is None:
        raise HTTPException(status_code=404, detail="Event not found")

    return schemas.EventOut(
        id=e.id,
        object_id=e.object_id,
        owner_id=e.owner_id,
        bbox=e.bbox,
        frame_snapshot_url=build_snapshot_url(e.frame_snapshot_path),
        status=e.status.value,
        event_timestamp=e.event_timestamp,
        created_at=e.created_at,
        updated_at=e.updated_at,
    )


@router.patch("/{event_id}", response_model=schemas.EventOut)
def update_event_status_endpoint(
    event_id: int,
    data: schemas.EventStatusUpdate,
    db: Session = Depends(get_db),
):
    mapping = {
        "new": models.EventStatus.new,
        "confirmed": models.EventStatus.confirmed,
        "dismissed": models.EventStatus.dismissed,
    }
    new_status = mapping[data.status]

    event = crud.update_event_status(db, event_id, new_status)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    return to_event_out(event)