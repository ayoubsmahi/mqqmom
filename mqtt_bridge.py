import serial
import paho.mqtt.client as mqtt
import time

SERIAL_PORT = "/dev/ttyACM0"
BAUD_RATE = 9600
BROKER = "localhost"
AIR_QUALITY_TOPIC = "sensors/air_quality"
FAN_CONTROL_TOPIC = "devices/fan/control"

ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)


def on_connect(client, userdata, flags, reason_code, properties=None):
    rc = reason_code.value if hasattr(reason_code, "value") else reason_code
    if rc == 0:
        client.subscribe(FAN_CONTROL_TOPIC)
        print(f"Subscribed to {FAN_CONTROL_TOPIC}")
    else:
        print(f"MQTT connect failed: {rc}")


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


try:
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
except (AttributeError, TypeError):
    client = mqtt.Client()

client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, 1883)
client.loop_start()

print(f"Two-way bridge on {SERIAL_PORT}")
print(f"  Serial → MQTT: {AIR_QUALITY_TOPIC}")
print(f"  MQTT → Serial: {FAN_CONTROL_TOPIC}")

while True:
    try:
        line = ser.readline().decode("utf-8").strip()
        if not line:
            continue

        print(f"  → {line}")

        if line.isdigit():
            client.publish(AIR_QUALITY_TOPIC, line)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(1)
