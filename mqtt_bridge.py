#!/usr/bin/env python3
"""Bridge Arduino serial ↔ MQTT, or run in --simulate mode without hardware."""

import argparse
import random
import sys
import time

import paho.mqtt.client as mqtt

BROKER = "localhost"
PORT = 1883
AIR_QUALITY_TOPIC = "sensors/air_quality"
FAN_CONTROL_TOPIC = "devices/fan/control"
READ_INTERVAL_S = 2.0
BAUD_RATE = 9600
DEFAULT_SERIAL_PORT = "/dev/ttyACM0"


def make_client() -> mqtt.Client:
    try:
        return mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
    except (AttributeError, TypeError):
        return mqtt.Client()


def run_simulate() -> None:
    state = {"value": 200.0, "relay_on": False}

    def on_connect(client, userdata, flags, reason_code, properties=None):
        rc = reason_code.value if hasattr(reason_code, "value") else reason_code
        if rc == 0:
            client.subscribe(FAN_CONTROL_TOPIC)
            print(f"Subscribed to {FAN_CONTROL_TOPIC}")
        else:
            print(f"MQTT connect failed: {rc}", file=sys.stderr)

    def on_message(client, userdata, msg):
        if msg.topic != FAN_CONTROL_TOPIC:
            return

        command = msg.payload.decode("utf-8").strip()
        if command == "ON":
            state["relay_on"] = True
            print("  → Relay: ON (simulated)")
        elif command == "OFF":
            state["relay_on"] = False
            print("  → Relay: OFF (simulated)")
        else:
            print(f"  ← Ignoring unknown fan command: {command!r}")

    client = make_client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT)
    client.loop_start()

    print("Simulation mode (no Arduino required)")
    print(f"  Simulated sensor → MQTT: {AIR_QUALITY_TOPIC}")
    print(f"  MQTT → Simulated relay: {FAN_CONTROL_TOPIC}")

    try:
        while True:
            drift = random.uniform(-8, 12)
            if state["relay_on"]:
                drift -= 25
            state["value"] = max(100, min(500, state["value"] + drift))
            reading = int(state["value"])
            print(f"  → {reading}")
            client.publish(AIR_QUALITY_TOPIC, str(reading))
            time.sleep(READ_INTERVAL_S)
    except KeyboardInterrupt:
        print("\nBridge stopped.")
    finally:
        client.loop_stop()
        client.disconnect()


def run_serial(serial_port: str) -> None:
    import serial

    ser = serial.Serial(serial_port, BAUD_RATE, timeout=2)

    def on_connect(client, userdata, flags, reason_code, properties=None):
        rc = reason_code.value if hasattr(reason_code, "value") else reason_code
        if rc == 0:
            client.subscribe(FAN_CONTROL_TOPIC)
            print(f"Subscribed to {FAN_CONTROL_TOPIC}")
        else:
            print(f"MQTT connect failed: {rc}", file=sys.stderr)

    def on_message(client, userdata, msg):
        if msg.topic != FAN_CONTROL_TOPIC:
            return

        command = msg.payload.decode("utf-8").strip()
        if command not in ("ON", "OFF"):
            print(f"  ← Ignoring unknown fan command: {command!r}")
            return

        ser.write(f"{command}\n".encode("utf-8"))
        ser.flush()
        print(f"  ← {command} sent to Arduino")

    client = make_client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT)
    client.loop_start()

    print(f"Two-way bridge on {serial_port}")
    print(f"  Serial → MQTT: {AIR_QUALITY_TOPIC}")
    print(f"  MQTT → Serial: {FAN_CONTROL_TOPIC}")

    try:
        while True:
            try:
                line = ser.readline().decode("utf-8").strip()
                if not line:
                    continue

                print(f"  → {line}")

                if line.isdigit():
                    client.publish(AIR_QUALITY_TOPIC, line)
            except Exception as exc:
                print(f"Error: {exc}")
                time.sleep(1)
    except KeyboardInterrupt:
        print("\nBridge stopped.")
    finally:
        client.loop_stop()
        client.disconnect()
        ser.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Bridge Arduino serial ↔ MQTT")
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Run without hardware (generates sensor data internally)",
    )
    parser.add_argument(
        "--port",
        default=DEFAULT_SERIAL_PORT,
        help=f"Serial port for real/simulated Arduino (default: {DEFAULT_SERIAL_PORT})",
    )
    args = parser.parse_args()

    if args.simulate:
        run_simulate()
    else:
        run_serial(args.port)


if __name__ == "__main__":
    main()
