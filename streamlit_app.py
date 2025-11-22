import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="OPSD PowerDesk Dashboard", layout="wide")

# ============================
# COUNTRY SELECTOR
# ============================

COUNTRIES = ["CZ", "IE", "DK"]

country = st.sidebar.selectbox(
    "Select Country",
    COUNTRIES,
    index=0,
)

st.title(f"⚡ Live Forecast Dashboard — {country}")

# ============================================
# LOAD FILES (based on YOUR available files)
# ============================================

# 1-step forecast = LIVE forecast cone
fc_live = pd.read_csv(f"outputs/{country}_combined_forecasts_test_1step.csv")
fc_live["timestamp"] = pd.to_datetime(fc_live["timestamp"], utc=True)

# Anomaly file
anomalies = pd.read_csv(f"outputs/{country}_anomalies.csv")
anomalies["timestamp"] = pd.to_datetime(anomalies["timestamp"], utc=True)

# Online adaptation updates log
updates = pd.read_csv(f"outputs/{country}_online_updates.csv")
updates["timestamp"] = pd.to_datetime(updates["timestamp"], utc=True)

# ============================
# LIVE SERIES (7–14 days)
# ============================

st.subheader("📈 Live Series (Last 14 Days)")

last_days = fc_live.tail(24*14)

fig1 = go.Figure()

fig1.add_trace(go.Scatter(
    x=last_days["timestamp"],
    y=last_days["y_true"],
    name="Actual Load",
    line=dict(color="white")
))

fig1.add_trace(go.Scatter(
    x=last_days["timestamp"],
    y=last_days["yhat_sarima"],
    name="Forecast (SARIMA)",
    line=dict(color="cyan")
))

fig1.update_layout(
    template="plotly_dark",
    height=350
)

st.plotly_chart(fig1, use_container_width=True)

# ============================
# 24H FORECAST CONE (80% PI)
# ============================

st.subheader("🔮 24-hour Forecast Cone (80% Prediction Interval)")

next_24 = fc_live.tail(24)

fig2 = go.Figure()

fig2.add_trace(go.Scatter(
    x=next_24["timestamp"],
    y=next_24["hi_sarima"],
    name="Upper 80% PI",
    line=dict(width=0),
    showlegend=False
))

fig2.add_trace(go.Scatter(
    x=next_24["timestamp"],
    y=next_24["lo_sarima"],
    name="Lower 80% PI",
    fill="tonexty",
    line=dict(width=0),
    fillcolor="rgba(0,200,255,0.2)",
    showlegend=True
))

fig2.add_trace(go.Scatter(
    x=next_24["timestamp"],
    y=next_24["yhat_sarima"],
    name="Forecast Mean",
    line=dict(color="yellow")
))

fig2.update_layout(
    template="plotly_dark",
    height=350
)

st.plotly_chart(fig2, use_container_width=True)

# ============================
# ANOMALY TAPE
# ============================

st.subheader("🚨 Anomaly Tape (flag_z = 1)")

anom = anomalies[anomalies["flag_z"] == 1]

if len(anom) == 0:
    st.info("No anomalies detected.")
else:
    st.dataframe(anom.tail(20))

# ============================
# KPI TILES
# ============================

st.subheader("📊 Rolling 7-day KPIs")

# get last row from updates log
if len(updates) > 0:
    last_update = updates.iloc[-1]

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Rolling-7d MASE", f"{last_update['MASE7']:.3f}")
    col2.metric("Rolling-7d PI Coverage", f"{last_update['PI7']*100:.1f}%")
    col3.metric("# Anomaly Hours Today", int(last_update["anomaly_today"]))
    col4.metric("Last Update Time", str(last_update["timestamp"]))

else:
    st.warning("No online update records found.")

# ============================
# UPDATE STATUS
# ============================

st.subheader("🟢 Update Status")

if len(updates) > 0:
    st.write(f"**Last update:** {last_update['timestamp']} — Reason: **{last_update['reason']}**")
else:
    st.write("No update records found.")
