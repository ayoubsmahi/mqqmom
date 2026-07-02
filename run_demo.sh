#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if ! command -v mosquitto >/dev/null 2>&1; then
  echo "Mosquitto is not installed. Install it first, e.g.:"
  echo "  sudo pacman -S mosquitto"
  exit 1
fi

if ! pgrep -x mosquitto >/dev/null 2>&1; then
  echo "Starting Mosquitto broker..."
  if systemctl is-active --quiet mosquitto 2>/dev/null; then
    :
  elif systemctl list-unit-files mosquitto.service >/dev/null 2>&1; then
    sudo systemctl start mosquitto
  else
    mosquitto -d
  fi
  sleep 1
fi

if ! pgrep -x mosquitto >/dev/null 2>&1; then
  echo "Mosquitto is not running. Start it manually:"
  echo "  sudo systemctl start mosquitto"
  exit 1
fi

PYTHON="${PYTHON:-python3}"
if [[ -d .venv ]]; then
  PYTHON=".venv/bin/python"
fi

LOGGER_PID=""
BRIDGE_PID=""

cleanup() {
  [[ -n "$LOGGER_PID" ]] && kill "$LOGGER_PID" 2>/dev/null || true
  [[ -n "$BRIDGE_PID" ]] && kill "$BRIDGE_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "Starting db_logger_alerter.py..."
"$PYTHON" db_logger_alerter.py &
LOGGER_PID=$!
sleep 1

echo "Starting mqtt_bridge.py --simulate..."
"$PYTHON" mqtt_bridge.py --simulate &
BRIDGE_PID=$!
sleep 1

echo ""
echo "============================================"
echo "  MOM IoT Demo (simulated sensor node)"
echo "============================================"
echo ""
echo "  Dashboard:  streamlit run dashboard.py"
echo "              (starting now in this terminal)"
echo ""
echo "  Wireshark:  capture interface lo (loopback)"
echo "              display filter: mqtt"
echo ""
echo "  Topics to watch:"
echo "    sensors/air_quality   (sensor readings)"
echo "    devices/fan/control   (ON / OFF commands)"
echo ""
echo "  Press Ctrl+C to stop everything."
echo "============================================"
echo ""

exec "$PYTHON" -m streamlit run dashboard.py
