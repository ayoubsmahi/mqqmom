#!/usr/bin/env python3
"""Simulate the Elegoo Uno firmware over a serial port (matches src/main.cpp)."""

import argparse
import random
import sys
import time

import serial

BAUD_RATE = 9600
READ_INTERVAL_S = 2.0


def run(port: str) -> None:
    relay_on = False
    value = 200.0

    with serial.Serial(port, BAUD_RATE, timeout=0.1) as ser:
        print(f"Arduino simulator on {port} @ {BAUD_RATE} baud")
        print("  Out: MQ135 raw values every 2s")
        print("  In:  ON / OFF relay commands")
        last_read = time.monotonic()

        while True:
            line = ser.readline().decode("utf-8", errors="ignore").strip()
            if line == "ON":
                relay_on = True
                ser.write(b"Relay: ON\n")
                print("Relay: ON")
            elif line == "OFF":
                relay_on = False
                ser.write(b"Relay: OFF\n")
                print("Relay: OFF")

            now = time.monotonic()
            if now - last_read >= READ_INTERVAL_S:
                last_read = now
                drift = random.uniform(-8, 12)
                if relay_on:
                    drift -= 25
                value = max(100, min(500, value + drift))
                reading = int(value)
                ser.write(f"{reading}\n".encode())
                print(f"Sensor: {reading}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Simulate Elegoo Uno serial behavior for mqtt_bridge.py"
    )
    parser.add_argument(
        "port",
        nargs="?",
        help="Serial port (e.g. /dev/pts/4 from socat)",
    )
    args = parser.parse_args()

    if not args.port:
        parser.print_help()
        print(
            "\nExample with virtual serial pair:\n"
            "  socat -d -d pty,raw,echo=0 pty,raw,echo=0\n"
            "  python arduino_sim.py /dev/pts/4\n"
            "  python mqtt_bridge.py --port /dev/pts/5",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        run(args.port)
    except serial.SerialException as exc:
        print(f"Serial error: {exc}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nSimulator stopped.")


if __name__ == "__main__":
    main()
