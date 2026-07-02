# MOM IoT Demo Guide (No Hardware Required)

> **Präsentationstext:** Den vollständigen Sprechertext für die finale Präsentation  
> (Folien + Live-Demo + Wireshark) findest du in **`PRAESENTATION_FINAL.md`**.

Use this when the Elegoo Uno is unavailable. The software stack runs unchanged; only the
physical sensor node is simulated.

## Prerequisites

```bash
# Install Mosquitto broker (Arch Linux example)
sudo pacman -S mosquitto
sudo systemctl enable --now mosquitto

# Python dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Quick demo (recommended for meetings)

One command starts the logger, simulated bridge, and dashboard:

```bash
chmod +x run_demo.sh
./run_demo.sh
```

Open **http://localhost:8501** if Streamlit does not open automatically.

### What to show

1. **Live chart** — air quality readings update every ~2 seconds.
2. **Alert** — when the value rises above **300**, the dashboard shows a critical warning
   and the logger prints `CRITICAL WARNING`.
3. **Fan control** — click **Turn Fan ON** / **Turn Fan OFF**; the bridge terminal shows
   `Relay: ON (simulated)` or `Relay: OFF (simulated)`.
4. **Wireshark** — capture MQTT packets (see below).

---

## Wireshark capture

Because everything uses `localhost:1883`, capture on the **loopback** interface.

1. Open Wireshark.
2. Start capture on **`lo`** (not `wlan0` / `eth0`).
3. Apply display filter:

   ```
   mqtt
   ```

   Narrower filter:

   ```
   mqtt.topic contains "air_quality" or mqtt.topic contains "fan/control"
   ```

4. Look for:
   - **CONNECT** — clients joining the broker
   - **SUBSCRIBE** — logger and bridge subscribing to topics
   - **PUBLISH** on `sensors/air_quality` — numeric payloads (`245`, `312`, …)
   - **PUBLISH** on `devices/fan/control` — `ON` or `OFF` when you use the dashboard

### Linux note

Capturing on `lo` may require root or membership in the `wireshark` group.

### Manual test packets

With Mosquitto running:

```bash
mosquitto_pub -h localhost -t sensors/air_quality -m "350"
mosquitto_pub -h localhost -t devices/fan/control -m "ON"
```

These appear as PUBLISH frames in Wireshark even without the full stack.

---

## Full serial-path demo (optional)

This mirrors the real architecture: simulated Arduino → USB serial → bridge → MQTT.

### Terminal 1 — virtual serial pair

```bash
socat -d -d pty,raw,echo=0 pty,raw,echo=0
```

Note the two paths printed, e.g. `/dev/pts/3` and `/dev/pts/4`.

### Terminal 2 — Arduino simulator

```bash
python arduino_sim.py /dev/pts/3
```

### Terminal 3 — MQTT bridge (real serial mode)

```bash
python mqtt_bridge.py --port /dev/pts/4
```

### Terminal 4 — logger and dashboard

```bash
python db_logger_alerter.py
streamlit run dashboard.py
```

---

## Run components separately

| Component | Command |
|-----------|---------|
| Simulated bridge | `python mqtt_bridge.py --simulate` |
| Real / virtual serial bridge | `python mqtt_bridge.py --port /dev/ttyACM0` |
| Database logger | `python db_logger_alerter.py` |
| Dashboard | `streamlit run dashboard.py` |

---

## What to say if asked about the broken board

> The physical sensor node failed, so I'm running a software simulator that uses the same
> serial/MQTT protocol as the Elegoo Uno firmware. The IoT pipeline — MQTT broker, database,
> alerts, dashboard, and fan control — is unchanged and fully demonstrable, including live
> packet capture in Wireshark.
