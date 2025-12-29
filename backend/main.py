from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware

from db.base import Base, engine
from db import models
from api import events, streams, internal


app = FastAPI(title="Abandoned Object Detection API")

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(streams.router)
app.include_router(events.router)
app.include_router(internal.router)

SNAPSHOT_DIR = Path("snapshots")
SNAPSHOT_DIR.mkdir(exist_ok=True)

app.mount(
    "/snapshots",
    StaticFiles(directory=SNAPSHOT_DIR),
    name="snapshots",
)