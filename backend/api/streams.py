from fastapi import APIRouter

router = APIRouter(
    prefix="/streams",
    tags=["streams"],
)

HLS_URL = "http://localhost:8888/live_stream/index.m3u8"


@router.get("/hls")
def get_stream_hls():
    """
    Возвращает HLS-ссылку для единственного потока.
    """
    return {"hls_url": HLS_URL}
