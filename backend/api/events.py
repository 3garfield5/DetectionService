from typing import List, Optional
import os
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from db import crud, schemas, models
from db.base import get_db

router = APIRouter(prefix="/events", tags=["events"])

S3_BUCKET = os.getenv("S3_BUCKET", "snapshots")
S3_PUBLIC_ENDPOINT = os.getenv("S3_PUBLIC_ENDPOINT", "http://localhost:9000").rstrip("/")


def _is_http_url(value: str) -> bool:
    try:
        u = urlparse(value)
        return u.scheme in ("http", "https")
    except Exception:
        return False


def _object_key_from_maybe_url(value: str) -> str:
    """
    Поддержка старых данных:
    - если в БД лежит уже key:  "abc.jpg" -> вернем как есть
    - если лежит URL: "http://host:9000/bucket/abc.jpg" -> достанем "abc.jpg"
    """
    if not value:
        return value
    if not _is_http_url(value):
        return value

    u = urlparse(value)
    path = u.path.lstrip("/")
    parts = path.split("/", 1)
    if len(parts) == 2 and parts[0] == S3_BUCKET:
        return parts[1]
    return parts[-1] if parts else value


def build_snapshot_url(path_or_key: Optional[str]) -> Optional[str]:
    if not path_or_key:
        return None
    key = _object_key_from_maybe_url(path_or_key)
    return f"{S3_PUBLIC_ENDPOINT}/{S3_BUCKET}/{key}"


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
    return [to_event_out(e) for e in events]


@router.get("/{event_id}", response_model=schemas.EventOut)
def get_event(
    event_id: int,
    db: Session = Depends(get_db),
):
    e = crud.get_event(db, event_id)
    if e is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return to_event_out(e)


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
