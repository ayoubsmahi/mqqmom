# MOM IoT — Air Quality Monitoring System

An end-to-end IoT pipeline that reads air quality from an MQ135 sensor on an Arduino Uno, publishes data over MQTT, logs readings to SQLite, raises alerts when air quality is poor, and lets you control a fan relay from a web dashboard.

The stack can run with real hardware or entirely in software using the built-in simulator — useful for demos and development when the board is unavailable.

## Architecture

```
┌─────────────────┐     serial      ┌──────────────┐     MQTT      ┌─────────────────┐
│  Arduino Uno    │ ◄──────────────►│  mqtt_bridge │ ◄───────────► │  Mosquitto      │
│  MQ135 + relay  │                 │  (Python)    │               │  localhost:1883 │
└─────────────────┘                 └──────────────┘               └────────┬────────┘
                                                                              │
                                    ┌─────────────────────────────────────────┼──────────────┐
                                    │                                         │              │
                                    ▼                                         ▼              ▼
                           ┌────────────────┐                        ┌──────────────┐  ┌───────────┐
                           │ db_logger_     │                        │ dashboard.py │  │ Wireshark │
                           │ alerter.py     │                        │ (Streamlit)  │  │ (optional)│
                           │ → SQLite       │                        │ fan control  │  └───────────┘
                           └────────────────┘                        └──────────────┘
```

### MQTT topics

| Topic | Direction | Payload |
|-------|-----------|---------|
| `sensors/air_quality` | Sensor → broker | Numeric raw ADC reading (e.g. `245`) |
| `devices/fan/control` | Dashboard → broker | `ON` or `OFF` |

### Alert threshold

Readings above **300** trigger a critical warning in both the logger and the dashboard.

## Hardware

| Component | Connection |
|-----------|------------|
| MQ135 air quality sensor | Analog pin **A0** |
| Fan relay module | Digital pin **8** |
| Serial | **9600** baud (USB) |

Firmware is in `src/main.cpp` and targets an **Arduino Uno** (Elegoo-compatible). Build and upload with [PlatformIO](https://platformio.org/):

```bash
pio run -t upload
pio device monitor
```

## Software components

| File | Role |
|------|------|
| `src/main.cpp` | Reads MQ135 every 2 s, prints raw values on serial; accepts `ON`/`OFF` relay commands |
| `mqtt_bridge.py` | Bridges serial ↔ MQTT, or runs in `--simulate` mode without hardware |
| `db_logger_alerter.py` | Subscribes to sensor topic, writes to `air_quality_data.db`, prints alerts |
| `dashboard.py` | Streamlit UI — live chart, alert status, fan ON/OFF buttons |
| `arduino_sim.py` | Simulates the Uno firmware over a virtual serial port |
| `run_demo.sh` | One-command demo (logger + simulated bridge + dashboard) |

## Prerequisites

- **Mosquitto** MQTT broker on `localhost:1883`
- **Python 3** with dependencies from `requirements.txt`
- **PlatformIO** (only for building/uploading firmware)

### Install (Arch Linux example)

```bash
# MQTT broker
sudo pacman -S mosquitto
sudo systemctl enable --now mosquitto

# Python environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Quick start (simulated demo)

No Arduino required. Starts the logger, simulated bridge, and dashboard:

```bash
chmod +x run_demo.sh
./run_demo.sh
```

Open **http://localhost:8501** if Streamlit does not launch automatically.

**What to try:**

1. Watch the live chart update every ~2 seconds.
2. Wait for a reading above **300** — the dashboard shows a critical warning and the logger prints `CRITICAL WARNING`.
3. Click **Turn Fan ON** / **Turn Fan OFF** — the bridge logs `Relay: ON (simulated)` or `Relay: OFF (simulated)`.
4. In simulation mode, turning the fan on gradually lowers readings.

## Run with real hardware

### 1. Flash the Arduino

Connect the Uno via USB (default port `/dev/ttyACM0` in `platformio.ini`) and upload:

```bash
pio run -t upload
```

### 2. Start the stack

In separate terminals:

```bash
python db_logger_alerter.py
python mqtt_bridge.py --port /dev/ttyACM0
streamlit run dashboard.py
```

Ensure Mosquitto is running before starting the Python services.

## Run components separately

| Component | Command |
|-----------|---------|
| Simulated bridge (no hardware) | `python mqtt_bridge.py --simulate` |
| Real / virtual serial bridge | `python mqtt_bridge.py --port /dev/ttyACM0` |
| Database logger | `python db_logger_alerter.py` |
| Dashboard | `streamlit run dashboard.py` |

## Full serial-path demo (virtual port)

Mirrors the real architecture using a virtual serial pair instead of USB:

**Terminal 1 — create virtual serial pair:**

```bash
socat -d -d pty,raw,echo=0 pty,raw,echo=0
```

Note the two paths printed (e.g. `/dev/pts/3` and `/dev/pts/4`).

**Terminal 2 — Arduino simulator:**

```bash
python arduino_sim.py /dev/pts/3
```

**Terminal 3 — MQTT bridge:**

```bash
python mqtt_bridge.py --port /dev/pts/4
```

**Terminal 4 — logger and dashboard:**

```bash
python db_logger_alerter.py
streamlit run dashboard.py
```

## Wireshark (optional)

Because everything uses `localhost:1883`, capture on the **loopback** interface (`lo`).

1. Start capture on `lo`.
2. Apply display filter: `mqtt`
3. Narrower filter: `mqtt.topic contains "air_quality" or mqtt.topic contains "fan/control"`

Look for **CONNECT**, **SUBSCRIBE**, and **PUBLISH** frames on the topics above.

Manual test packets (with Mosquitto running):

```bash
mosquitto_pub -h localhost -t sensors/air_quality -m "350"
mosquitto_pub -h localhost -t devices/fan/control -m "ON"
```

On Linux, capturing on `lo` may require root or membership in the `wireshark` group.

## Database

Readings are stored in `air_quality_data.db` (SQLite):

```sql
CREATE TABLE sensor_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    value REAL
);
```

The dashboard shows the 50 most recent entries.

## Project structure

```
air_qualitz_mqq/
├── src/main.cpp           # Arduino firmware
├── platformio.ini         # PlatformIO config (Uno, 9600 baud)
├── mqtt_bridge.py         # Serial ↔ MQTT bridge
├── db_logger_alerter.py   # MQTT subscriber + SQLite logger
├── dashboard.py           # Streamlit web dashboard
├── arduino_sim.py         # Serial firmware simulator
├── run_demo.sh            # One-command demo launcher
├── requirements.txt       # Python dependencies
├── air_quality_data.db    # SQLite database (created at runtime)
└── DEMO.md                # Extended demo guide
```

## License

See repository history for authorship. Add a license file if you plan to distribute this project.
