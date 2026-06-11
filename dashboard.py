#!/usr/bin/env python3

import sqlite3
import time
from pathlib import Path

import pandas as pd
import paho.mqtt.publish as publish
import streamlit as st

BROKER = "localhost"
PORT = 1883
FAN_TOPIC = "devices/fan/control"
DATABASE = Path(__file__).parent / "air_quality_data.db"
ALERT_THRESHOLD = 300
REFRESH_SECONDS = 2

st.set_page_config(page_title="MOM IoT Dashboard", layout="wide")


@st.cache_data(ttl=2)
def fetch_sensor_data() -> pd.DataFrame:
    conn = sqlite3.connect(DATABASE)
    df = pd.read_sql_query(
        """
        SELECT id, timestamp, value
        FROM sensor_logs
        ORDER BY id DESC
        LIMIT 50
        """,
        conn,
    )
    conn.close()

    if df.empty:
        return df

    df = df.sort_values("id").reset_index(drop=True)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def send_fan_command(command: str) -> None:
    publish.single(command, hostname=BROKER, port=PORT, topic=FAN_TOPIC)


st.title("MOM IoT Dashboard")

df = fetch_sensor_data()

if df.empty:
    st.info("No sensor data yet. Start the bridge and logger to collect readings.")
else:
    latest_value = float(df["value"].iloc[-1])

    if latest_value > ALERT_THRESHOLD:
        st.metric(
            label="🚨 Current Air Quality (CRITICAL)",
            value=f"{latest_value:g}",
            delta="Poor air quality detected",
            delta_color="inverse",
        )
    else:
        st.metric(label="Current Air Quality", value=f"{latest_value:g}")

    st.subheader("Historical Readings")
    chart_df = df.set_index("timestamp")[["value"]]
    st.line_chart(chart_df)

st.subheader("Device Control")

col_on, col_off = st.columns(2)

with col_on:
    if st.button("Turn Fan ON", use_container_width=True):
        send_fan_command("ON")
        st.success("Sent ON to devices/fan/control")

with col_off:
    if st.button("Turn Fan OFF", use_container_width=True):
        send_fan_command("OFF")
        st.success("Sent OFF to devices/fan/control")

st.caption(f"Auto-refreshing every {REFRESH_SECONDS} seconds")

time.sleep(REFRESH_SECONDS)
st.rerun()
