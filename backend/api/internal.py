import base64
import os
from uuid import uuid4
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

import boto3
from botocore.client import Config
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db import crud, schemas
from db.base import get_db

router = APIRouter(prefix="/internal", tags=["internal"])

S3_ENDPOINT = os.getenv("S3_ENDPOINT", "http://minio:9000").rstrip("/")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "")
S3_BUCKET = os.getenv("S3_BUCKET", "snapshots")
S3_SECURE = os.getenv("S3_SECURE", "false").lower() == "true"

S3_PUBLIC_ENDPOINT = os.getenv("S3_PUBLIC_ENDPOINT", "http://localhost:9000").rstrip("/")

s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    config=Config(signature_version="s3v4"),
    verify=S3_SECURE,
)


def _is_http_url(value: str) -> bool:
    try:
        u = urlparse(value)
        return u.scheme in ("http", "https")
    except Exception:
        return False


def _build_public_url(object_key: str) -> str:
    return f"{S3_PUBLIC_ENDPOINT}/{S3_BUCKET}/{object_key}"


def _object_key_from_maybe_url(value: str) -> str:
    """
    Если в БД/входе уже лежит URL вида http://host:9000/bucket/key.jpg,
    вытащим key.jpg. Если это уже key — вернём как есть.
    """
    if not value:
        return value
    if not _is_http_url(value):
        return value

    u = urlparse(value)
    path = u.path.lstrip("/")
    if not path:
        return value
    parts = path.split("/", 1)
    if len(parts) == 2 and parts[0] == S3_BUCKET:
        return parts[1]
    return parts[-1] if parts else value


def _timestamp_to_int(ts: datetime) -> int:
    return int(ts.timestamp())


@router.post("/events", response_model=schemas.EventOut)
def create_event_internal(
    data: schemas.EventCreateInternal,
    db: Session = Depends(get_db),
):
    snapshot_key: Optional[str] = None

    if data.frame_snapshot_path:
        snapshot_key = _object_key_from_maybe_url(data.frame_snapshot_path)

    elif data.frame_snapshot_base64:
        try:
            image_bytes = base64.b64decode(data.frame_snapshot_base64)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid base64 image")

        filename = f"{_timestamp_to_int(data.timestamp)}_{uuid4().hex}.jpg"
        snapshot_key = filename

        try:
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=snapshot_key,
                Body=image_bytes,
                ContentType="image/jpeg",
            )
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"S3 upload failed: {e}")

    else:
        raise HTTPException(
            status_code=400,
            detail="Either frame_snapshot_base64 or frame_snapshot_path must be provided",
        )

    data_for_db = data.model_copy(update={"frame_snapshot_path": snapshot_key})

    e = crud.create_event(db, data_for_db)

    object_key = _object_key_from_maybe_url(e.frame_snapshot_path) if e.frame_snapshot_path else ""
    return schemas.EventOut(
        id=e.id,
        object_id=e.object_id,
        owner_id=e.owner_id,
        bbox=e.bbox,
        frame_snapshot_url=_build_public_url(object_key) if object_key else None,
        status=e.status.value,
        event_timestamp=e.event_timestamp,
        created_at=e.created_at,
        updated_at=e.updated_at,
    )
