import logging
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .api import router as api_router
from .db import get_db
from .config import settings
import sqlite3

app = FastAPI(title="SmartHome Backend")

# logging
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger("smarthome")


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/health")
async def health(conn=Depends(get_db)):
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1")
        return {"status": "ok"}
    except Exception as exc:
        logger.exception("Health check failed: %s", exc)
        raise HTTPException(status_code=500, detail="db unreachable")


# Enable CORS so the frontend served from a different port/file system can call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="")

