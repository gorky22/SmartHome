from fastapi import APIRouter, Depends, HTTPException, status
from .schemas import Item
from .db import get_db, init_db, log_data, list_devices, list_sensors, get_sensor_logs, sensor_stats
from .auth import require_api_key
import logging

router = APIRouter()
logger = logging.getLogger("smarthome.api")


@router.post("/items/", status_code=status.HTTP_201_CREATED)
async def create_item(item: Item, conn=Depends(get_db), _=Depends(require_api_key)):
    try:
        init_db(conn)
        log_data(item.dict(), conn)
        logger.info("Logged data for device %s", item.device)
        return {"item": item.dict()}
    except Exception:
        logger.exception("Failed to log data")
        raise HTTPException(status_code=500, detail="failed to save data")


@router.get("/devices")
async def api_list_devices(conn=Depends(get_db)):
    return list_devices(conn)


@router.get("/devices/{device_id}/sensors")
async def api_list_sensors(device_id: int, conn=Depends(get_db)):
    return list_sensors(conn, device_id)


@router.get("/devices/{device_id}/sensors/{sensor_id}/logs")
async def api_sensor_logs(device_id: int, sensor_id: int, start: str | None = None, end: str | None = None, limit: int = 1000, conn=Depends(get_db)):
    # validation: ensure sensor belongs to device
    sensors = list_sensors(conn, device_id)
    if not any(s["id"] == sensor_id for s in sensors):
        raise HTTPException(status_code=404, detail="sensor not found for device")
    return get_sensor_logs(conn, sensor_id, start=start, end=end, limit=limit)


@router.get("/devices/{device_id}/sensors/{sensor_id}/stats")
async def api_sensor_stats(device_id: int, sensor_id: int, start: str | None = None, end: str | None = None, conn=Depends(get_db)):
    # validation: ensure sensor belongs to device
    sensors = list_sensors(conn, device_id)
    if not any(s["id"] == sensor_id for s in sensors):
        raise HTTPException(status_code=404, detail="sensor not found for device")
    return sensor_stats(conn, sensor_id, start=start, end=end)
