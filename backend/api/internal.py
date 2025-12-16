import base64
from uuid import uuid4
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db import crud
from db.base import get_db
from db import schemas

router = APIRouter(prefix="/internal", tags=["internal"])

SNAPSHOT_BASE_URL = "https://example.com/snapshots/"
SNAPSHOT_DIR = Path("snapshots")
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)


def build_snapshot_url(path: str) -> str:
    return SNAPSHOT_BASE_URL.rstrip("/") + "/" + path.lstrip("/")


@router.post("/events", response_model=schemas.EventOut)
def create_event_internal(
    data: schemas.EventCreateInternal,
    db: Session = Depends(get_db),
):
    # 1. Получаем путь к файлу кадра
    if data.frame_snapshot_path:
        # Если уже прислали путь — просто используем его
        snapshot_path = data.frame_snapshot_path

    elif data.frame_snapshot_base64:
        # Если прислали base64 — декодируем и сохраняем
        try:
            image_bytes = base64.b64decode(data.frame_snapshot_base64)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid base64 image")

        filename = f"{int(data.timestamp.timestamp())}_{uuid4().hex}.jpg"
        filepath = SNAPSHOT_DIR / filename
        filepath.write_bytes(image_bytes)
        snapshot_path = filename
    else:
        raise HTTPException(
            status_code=400,
            detail="Either frame_snapshot_base64 or frame_snapshot_path must be provided",
        )

    # 2. Обновляем данные для записи в БД (подставляем путь)
    data_for_db = data.model_copy(update={"frame_snapshot_path": snapshot_path})

    # 3. Пишем событие в БД
    e = crud.create_event(db, data_for_db)

    # 4. Отдаём DTO для фронта
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
