"""Backward-compatible entry point. The real app lives in backend.app.* modules.

This module intentionally re-exports the important objects so existing tests
and external callers can continue to import `backend.main.app` and `backend.main.init_db`.
"""

from backend.app.main import app  # re-export the FastAPI app
from backend.app import db

# re-export helpers used by tests / scripts
init_db = db.init_db
get_db = db.get_db


if __name__ == "__main__":
    import os
    import uvicorn

    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host=host, port=port)
"""Backward-compatible entry point. The real app lives in backend.app.* modules.

This module intentionally re-exports the important objects so existing tests
and external callers can continue to import `backend.main.app` and `backend.main.init_db`.
"""

from backend.app.main import app  # re-export the FastAPI app
from backend.app import db

# re-export helpers used by tests / scripts
init_db = db.init_db
get_db = db.get_db


if __name__ == "__main__":
    import os
    import uvicorn

    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host=host, port=port)

"""Backward-compatible entry point. The real app lives in backend.app.* modules.

This module intentionally re-exports the important objects so existing tests
and external callers can continue to import `backend.main.app` and `backend.main.init_db`.
"""

from backend.app.main import app  # re-export the FastAPI app
from backend.app import db

# re-export helpers used by tests / scripts
init_db = db.init_db
get_db = db.get_db

def get_or_create_device(conn, name, mac_address=None, location=None, ip_address=None):
    cur = conn.cursor()
    cur.execute("SELECT id FROM devices WHERE mac_address = ?", (mac_address,))
    row = cur.fetchone()
    if row:
        device_id = row[0]
        cur.execute(
            "UPDATE devices SET last_seen = ?, ip_address = ? WHERE id = ?",
            (datetime.now(timezone.utc).isoformat(), ip_address, device_id)
        )
    else:
        cur.execute(
            "INSERT INTO devices (name, mac_address, location, ip_address, last_seen) VALUES (?, ?, ?, ?, ?)",
            (name, mac_address, location, ip_address, datetime.now(timezone.utc).isoformat())
        )
        device_id = cur.lastrowid
    conn.commit()
    return device_id


def get_or_create_sensor(conn, device_id, sensor_type, unit=None, pin=None):
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM sensors WHERE device_id = ? AND type = ?",
        (device_id, sensor_type)
    )
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute(
        "INSERT INTO sensors (device_id, type, unit, pin) VALUES (?, ?, ?, ?)",
        (device_id, sensor_type, unit, pin)
    )
    conn.commit()
    return cur.lastrowid


def log_sensor_reading(conn, sensor_id, value, status="ok"):
    cur = conn.cursor()
    now_iso = datetime.now(timezone.utc).isoformat()
    cur.execute(
        "INSERT INTO sensor_logs (sensor_id, value, status, timestamp, received_at) VALUES (?, ?, ?, ?, ?)",
        (sensor_id, value, status, now_iso, now_iso)
    )
    conn.commit()


def init_db(conn: sqlite3.Connection) -> None:
    """Create tables if they don't exist (idempotent)."""
    cur = conn.cursor()
    cur.executescript(
        """
        -- Table: devices
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            mac_address TEXT UNIQUE,
            location TEXT,
            ip_address TEXT,
            last_seen TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Table: sensors
        CREATE TABLE IF NOT EXISTS sensors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
            type TEXT NOT NULL,
            pin TEXT,
            unit TEXT,
            calibration_factor REAL DEFAULT 1.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Table: sensor_logs
        CREATE TABLE IF NOT EXISTS sensor_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor_id INTEGER NOT NULL REFERENCES sensors(id) ON DELETE CASCADE,
            value REAL NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'ok'
        );

        -- Table: alerts
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor_id INTEGER REFERENCES sensors(id),
            message TEXT NOT NULL,
            severity TEXT DEFAULT 'info',
            triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    conn.commit()


def log_data(payload, conn: sqlite3.Connection):
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
    # expect conn to be an existing sqlite3.Connection with foreign_keys enabled
    device_id = get_or_create_device(
        conn,
        name=payload.get("device", "Unknown Device"),
        mac_address=payload.get("mac"),
        location=payload.get("location"),
        ip_address=payload.get("ip")
    )

    for reading in payload.get("readings", []):
        sensor_id = get_or_create_sensor(
            conn,
            device_id=device_id,
            sensor_type=reading["sensor_type"],
            unit=reading.get("unit")
        )
        log_sensor_reading(conn, sensor_id, reading["value"])

@app.get("/")
async def root():
    return {"message": "Hello World"}

class Reading(BaseModel):
    sensor_type: str
    value: float
    unit: Optional[str]

class Item(BaseModel):
    device: str
    mac: Optional[str] = None
    ip: Optional[str] = None
    location: Optional[str] = None
    readings: List[Reading]


def get_db() -> Generator[sqlite3.Connection, None, None]:
    """FastAPI dependency that yields a DB connection for the request."""
    db_path = os.environ.get("DB_FILE", DB_FILE)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        yield conn
    finally:
        conn.close()


@app.post("/items/", status_code=status.HTTP_201_CREATED)
async def create_item(item: Item, conn: sqlite3.Connection = Depends(get_db)):
    try:
        # ensure the schema is present (safe no-op if already created)
        init_db(conn)

        payload = item.dict()
        log_data(payload, conn)
        logger.info("Logged data for device %s", payload.get("device"))
        return {"item": payload}
    except Exception as exc:  # narrow later
        logger.exception("Failed to log data: %s", exc)
        raise HTTPException(status_code=500, detail="failed to save data")


@app.get("/health")
async def health(conn: sqlite3.Connection = Depends(get_db)):
    """Simple health check: ensure DB is reachable and schema present."""
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1")
        return {"status": "ok"}
    except Exception as exc:
        logger.exception("Health check failed: %s", exc)
        raise HTTPException(status_code=500, detail="db unreachable")

if __name__ == "__main__":
    import uvicorn
    # 👇 Make it visible to other devices (like ESP8266)
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host=host, port=port)