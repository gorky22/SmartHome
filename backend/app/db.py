import sqlite3
from datetime import datetime, timezone
from typing import Generator

from .config import settings
DB_FILE = settings.db_file


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


def get_db() -> Generator[sqlite3.Connection, None, None]:
    db_path = settings.db_file
    conn = sqlite3.connect(db_path, check_same_thread=False)
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        yield conn
    finally:
        conn.close()


def get_or_create_device(conn, name, mac_address=None, location=None, ip_address=None):
    cur = conn.cursor()
    cur.execute("SELECT id FROM devices WHERE mac_address = ?", (mac_address,))
    row = cur.fetchone()
    if row:
        device_id = row[0]
        cur.execute(
            "UPDATE devices SET last_seen = ?, ip_address = ? WHERE id = ?",
            (datetime.now(timezone.utc).isoformat(), ip_address, device_id),
        )
    else:
        cur.execute(
            "INSERT INTO devices (name, mac_address, location, ip_address, last_seen) VALUES (?, ?, ?, ?, ?)",
            (name, mac_address, location, ip_address, datetime.now(timezone.utc).isoformat()),
        )
        device_id = cur.lastrowid
    conn.commit()
    return device_id


def get_or_create_sensor(conn, device_id, sensor_type, unit=None, pin=None):
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM sensors WHERE device_id = ? AND type = ?", (device_id, sensor_type)
    )
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute(
        "INSERT INTO sensors (device_id, type, unit, pin) VALUES (?, ?, ?, ?)",
        (device_id, sensor_type, unit, pin),
    )
    conn.commit()
    return cur.lastrowid


def log_sensor_reading(conn, sensor_id, value, status="ok"):
    cur = conn.cursor()
    now_iso = datetime.now(timezone.utc).isoformat()
    cur.execute(
        "INSERT INTO sensor_logs (sensor_id, value, status, timestamp, received_at) VALUES (?, ?, ?, ?, ?)",
        (sensor_id, value, status, now_iso, now_iso),
    )
    conn.commit()


def log_data(payload, conn: sqlite3.Connection):
    device_id = get_or_create_device(
        conn,
        name=payload.get("device", "Unknown Device"),
        mac_address=payload.get("mac"),
        location=payload.get("location"),
        ip_address=payload.get("ip"),
    )

    for reading in payload.get("readings", []):
        sensor_id = get_or_create_sensor(
            conn, device_id=device_id, sensor_type=reading["sensor_type"], unit=reading.get("unit")
        )
        log_sensor_reading(conn, sensor_id, reading["value"])


def list_devices(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.execute("SELECT id, name, mac_address, location, ip_address, last_seen, created_at FROM devices ORDER BY last_seen DESC")
    rows = cur.fetchall()
    return [
        {
            "id": r[0],
            "name": r[1],
            "mac": r[2],
            "location": r[3],
            "ip": r[4],
            "last_seen": r[5],
            "created_at": r[6],
        }
        for r in rows
    ]


def list_sensors(conn: sqlite3.Connection, device_id: int):
    cur = conn.cursor()
    cur.execute("SELECT id, type, unit, pin, calibration_factor, created_at FROM sensors WHERE device_id = ?", (device_id,))
    rows = cur.fetchall()
    return [
        {
            "id": r[0],
            "type": r[1],
            "unit": r[2],
            "pin": r[3],
            "calibration_factor": r[4],
            "created_at": r[5],
        }
        for r in rows
    ]


def get_sensor_logs(conn: sqlite3.Connection, sensor_id: int, start=None, end=None, limit: int = 1000):
    cur = conn.cursor()
    params = [sensor_id]
    q = "SELECT id, value, status, timestamp, received_at FROM sensor_logs WHERE sensor_id = ?"
    if start:
        q += " AND timestamp >= ?"
        params.append(start)
    if end:
        q += " AND timestamp <= ?"
        params.append(end)
    q += " ORDER BY timestamp ASC LIMIT ?"
    params.append(limit)
    cur.execute(q, tuple(params))
    rows = cur.fetchall()
    return [
        {"id": r[0], "value": r[1], "status": r[2], "timestamp": r[3], "received_at": r[4]} for r in rows
    ]


def sensor_stats(conn: sqlite3.Connection, sensor_id: int, start=None, end=None):
    cur = conn.cursor()
    params = [sensor_id]
    q = "SELECT COUNT(value), AVG(value), MIN(value), MAX(value) FROM sensor_logs WHERE sensor_id = ?"
    if start:
        q += " AND timestamp >= ?"
        params.append(start)
    if end:
        q += " AND timestamp <= ?"
        params.append(end)
    cur.execute(q, tuple(params))
    row = cur.fetchone()
    return {"count": row[0] or 0, "avg": row[1], "min": row[2], "max": row[3]}
