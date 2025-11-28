import os
import sqlite3
import tempfile

import pytest
import importlib
from fastapi.testclient import TestClient

# don't import backend.main at module import time because tests set env vars
main = None


@pytest.fixture()
def tmp_db_path(tmp_path):
    db_file = tmp_path / "test_smarthome.db"
    return str(db_file)


def test_root():
    # reload module to ensure latest settings are applied
    global main
    main = importlib.reload(importlib.import_module("backend.main"))
    client = TestClient(main.app)
    r = client.get("/")
    assert r.status_code == 200
    assert r.json() == {"message": "Hello World"}


def test_health_and_create_item(tmp_db_path):
    # Use a file-backed DB so connections share the same data
    os.environ["DB_FILE"] = tmp_db_path

    # reload main so settings pick up DB_FILE
    global main
    main = importlib.reload(importlib.import_module("backend.main"))

    # Ensure schema exists on the file
    conn = sqlite3.connect(tmp_db_path, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    main.init_db(conn)
    conn.close()

    client = TestClient(main.app)

    # Health endpoint should pass
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"

    sample = {
        "device": "Test Device",
        "mac": "00:11:22:33:44:55",
        "ip": "192.168.1.2",
        "location": "Lab",
        "readings": [
            {"sensor_type": "temperature", "value": 21.5, "unit": "C"},
        ],
    }

    r = client.post("/items/", json=sample)
    assert r.status_code == 201
    j = r.json()
    assert j["item"]["device"] == "Test Device"

    # Validate something got into the DB
    conn = sqlite3.connect(tmp_db_path)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM sensor_logs")
    count = cur.fetchone()[0]
    conn.close()
    assert count >= 1


def test_items_requires_api_key_when_configured(tmp_db_path):
    # configure DB and API keys
    os.environ["DB_FILE"] = tmp_db_path
    os.environ["SENSORS_API_KEYS"] = "good-key,other-key"

    # reload main so settings pick up env vars
    global main
    main = importlib.reload(importlib.import_module("backend.main"))

    conn = sqlite3.connect(tmp_db_path, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    main.init_db(conn)
    conn.close()

    client = TestClient(main.app)

    sample = {
        "device": "Secured Device",
        "mac": "AA:BB:CC:11:22:33",
        "ip": "192.168.1.5",
        "location": "Vault",
        "readings": [{"sensor_type": "temperature", "value": 17.2, "unit": "C"}],
    }

    # Missing key -> 401
    r = client.post("/items/", json=sample)
    assert r.status_code == 401

    # Wrong key -> 403
    r = client.post("/items/", json=sample, headers={"X-API-Key": "bad"})
    assert r.status_code == 403

    # Correct key -> success
    r = client.post("/items/", json=sample, headers={"X-API-Key": "good-key"})
    assert r.status_code == 201

    # Clean up keys so other tests aren't impacted
    del os.environ["SENSORS_API_KEYS"]
