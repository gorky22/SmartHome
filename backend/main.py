from fastapi import FastAPI
import sqlite3
from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional
import json

DB_FILE = "smarthome.db"

app = FastAPI()

def log_sensor_reading(conn, sensor_id, value, status="ok"):
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO sensor_logs (sensor_id, value, status, timestamp, received_at) VALUES (?, ?, ?, ?, ?)",
        (sensor_id, value, status, datetime.now(), datetime.now())
    )
    conn.commit()

def log_data(payload):
    """
    Example payload:
    {
        "device": "Living Room ESP32",
        "mac": "AA:BB:CC:DD:EE:FF",
        "ip": "192.168.1.42",
        "location": "Living Room",
        "readings": [
            {"sensor_type": "temperature", "value": 22.7, "unit": "°C"},
            {"sensor_type": "humidity", "value": 51.3, "unit": "%"}
        ]
    }
    """
    conn = sqlite3.connect(DB_FILE)
   

    for reading in payload.get("readings", []):
       
        log_sensor_reading(conn, '1', reading["value"])

    conn.close()



@app.get("/")
async def root():
    return {"message": "Hello World"}

class Reading(BaseModel):
    sensor_type: str
    value: float
    unit: Optional[str]

class Item(BaseModel):
    device: str
    mac: str
    ip: str
    location: str
    readings: List[Reading]

@app.post("/items/")
async def create_item(item: Item):
    log_data(json.loads(item.json()))
    return {"item": item}