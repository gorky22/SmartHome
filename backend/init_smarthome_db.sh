#!/usr/bin/env bash
# Smart Home Sensor Logging Database Setup (SQLite)

DB_FILE="smarthome.db"

# Remove old database if you want a clean start
if [ -f "$DB_FILE" ]; then
  echo "Removing old database: $DB_FILE"
  rm "$DB_FILE"
fi

echo "Creating new database: $DB_FILE"

sqlite3 "$DB_FILE" <<'EOF'
-- Table: devices
CREATE TABLE devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    mac_address TEXT UNIQUE,
    location TEXT,
    ip_address TEXT,
    last_seen TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: sensors
CREATE TABLE sensors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    type TEXT NOT NULL,
    pin TEXT,
    unit TEXT,
    calibration_factor REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: sensor_logs
CREATE TABLE sensor_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sensor_id INTEGER NOT NULL REFERENCES sensors(id) ON DELETE CASCADE,
    value REAL NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'ok'
);

-- Table: alerts
CREATE TABLE alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sensor_id INTEGER REFERENCES sensors(id),
    message TEXT NOT NULL,
    severity TEXT DEFAULT 'info',
    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Helpful indexes to make searches by device name / location and sensor type fast
CREATE INDEX IF NOT EXISTS idx_devices_name ON devices(name);
CREATE INDEX IF NOT EXISTS idx_devices_location ON devices(location);
CREATE INDEX IF NOT EXISTS idx_sensors_device_type ON sensors(device_id, type);
CREATE INDEX IF NOT EXISTS idx_sensor_logs_sensor_ts ON sensor_logs(sensor_id, timestamp);

-- Convenience view to make queries easier: joins logs with sensor and device info.
-- Example: SELECT * FROM device_sensor_logs WHERE device_name = 'Living Room ESP32' AND device_location = 'Living Room';
CREATE VIEW IF NOT EXISTS device_sensor_logs AS
SELECT
    sl.id as log_id,
    sl.sensor_id,
    s.type as sensor_type,
    s.unit as sensor_unit,
    s.pin as sensor_pin,
    s.device_id,
    d.name as device_name,
    d.mac_address as device_mac,
    d.ip_address as device_ip,
    d.location as device_location,
    sl.value,
    sl.timestamp,
    sl.received_at,
    sl.status
FROM sensor_logs sl
JOIN sensors s ON sl.sensor_id = s.id
JOIN devices d ON s.device_id = d.id;
EOF

echo "✅ Database schema created successfully!"
