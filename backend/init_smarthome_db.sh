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
EOF

echo "✅ Database schema created successfully!"
