from fastapi import APIRouter
import os

router = APIRouter(
    prefix="/streams",
    tags=["streams"],
)

HLS_PUBLIC_URL = os.getenv(
    "HLS_PUBLIC_URL",
)


@router.get("/hls")
def get_stream_hls():
    """
    Возвращает публичную HLS-ссылку для потока
    """
    return {
        "hls_url": HLS_PUBLIC_URL
    }
