#!/usr/bin/env python3

import sqlite3
import sys

import paho.mqtt.client as mqtt

BROKER = "localhost"
PORT = 1883
TOPIC = "sensors/air_quality"
DATABASE = "air_quality_data.db"
ALERT_THRESHOLD = 300


def setup_database(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sensor_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            value REAL
        )
        """
    )
    conn.commit()
    return conn


def on_connect(client, userdata, flags, reason_code, properties=None):
    rc = reason_code.value if hasattr(reason_code, "value") else reason_code
    if rc == 0:
        client.subscribe(TOPIC)
        print(f"Connected to MQTT broker, subscribed to {TOPIC}")
    else:
        print(f"MQTT connect failed: {rc}", file=sys.stderr)


def on_message(client, userdata, msg):
    conn = userdata["conn"]

    try:
        value = float(msg.payload.decode("utf-8").strip())
    except ValueError:
        print(f"Ignoring non-numeric payload: {msg.payload!r}")
        return

    conn.execute("INSERT INTO sensor_logs (value) VALUES (?)", (value,))
    conn.commit()

    if value > ALERT_THRESHOLD:
        print(f"🚨 CRITICAL WARNING: Poor Air Quality Detected! (Value: {value:g})")
    else:
        print(f"Logged sensor reading: {value:g}")


def main():
    conn = setup_database(DATABASE)
    print(f"Using database: {DATABASE}")

    try:
        client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
    except (AttributeError, TypeError):
        client = mqtt.Client()

    client.user_data_set({"conn": conn})
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(BROKER, PORT)
        print("Listening for sensor data... (Ctrl+C to stop)")
        client.loop_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        client.loop_stop()
        client.disconnect()
        conn.close()
        print("Database connection closed. Goodbye.")


if __name__ == "__main__":
    main()
