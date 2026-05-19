"""
Streamlit Dashboard — Distributed AI Smart Grid Simulator

Sections:
  1. System health banner
  2. Per-substation metric cards
  3. Load distribution bar chart
  4. Fault reports
  5. Live alert feed
  6. Historical trend charts (temperature, voltage, load)
"""
import streamlit as st
import requests
import time
import pandas as pd
from datetime import datetime
from collections import defaultdict

API_URL = "http://localhost:8000/state"

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Smart Grid AI Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .metric-card {
        background: #1e1e2e;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 8px;
    }
    .status-healthy  { color: #50fa7b; font-weight: bold; }
    .status-warning  { color: #ffb86c; font-weight: bold; }
    .status-critical { color: #ff5555; font-weight: bold; }
    .fault-badge {
        background: #ff5555;
        color: white;
        border-radius: 4px;
        padding: 2px 6px;
        font-size: 0.75em;
        margin-right: 4px;
    }
</style>
""", unsafe_allow_html=True)

# ── History buffers (kept across reruns via session_state) ────────────────────
if "history" not in st.session_state:
    st.session_state.history = defaultdict(lambda: {
        "voltage": [], "temperature": [], "load_percentage": [],
        "health_score": [], "timestamps": []
    })

MAX_HISTORY = 60   # data points to keep per substation

# ── Header ────────────────────────────────────────────────────────────────────
st.title("⚡ Distributed AI Smart Grid Simulator")
st.caption(f"Live monitoring dashboard  •  Polling {API_URL}")

placeholder = st.empty()

# ── Main loop ─────────────────────────────────────────────────────────────────
while True:
    try:
        response = requests.get(API_URL, timeout=3)
        if response.status_code != 200:
            with placeholder.container():
                st.warning(f"Backend returned HTTP {response.status_code}")
            time.sleep(2)
            continue

        data          = response.json()
        telemetry     = data.get("telemetry", {})
        health        = data.get("health", {})
        load_dist     = data.get("load_distribution", {})
        alerts        = data.get("alerts", [])
        fault_reports = data.get("fault_reports", {})

        active_subs = sorted(health.keys()) or ["S1", "S2", "S3"]

        # Update history buffers
        now_str = datetime.now().strftime("%H:%M:%S")
        for sub_id in active_subs:
            t = telemetry.get(sub_id, {})
            h = health.get(sub_id, {})
            buf = st.session_state.history[sub_id]
            buf["timestamps"].append(now_str)
            buf["voltage"].append(t.get("voltage", 0))
            buf["temperature"].append(t.get("temperature", 0))
            buf["load_percentage"].append(t.get("load_percentage", 0))
            buf["health_score"].append(h.get("health_score", 0))
            # Trim to MAX_HISTORY
            for key in buf:
                if len(buf[key]) > MAX_HISTORY:
                    buf[key] = buf[key][-MAX_HISTORY:]

        with placeholder.container():

            # ── System health banner ──────────────────────────────────────────
            critical_count = sum(1 for h in health.values() if h.get("risk_level") == "Critical")
            warning_count  = sum(1 for h in health.values() if h.get("risk_level") == "Warning")

            if critical_count > 0:
                st.error(f"🚨 SYSTEM ALERT: {critical_count} substation(s) in CRITICAL state")
            elif warning_count > 0:
                st.warning(f"⚠️ {warning_count} substation(s) in WARNING state")
            else:
                st.success("✅ All substations operating normally")

            # ── Substation cards ──────────────────────────────────────────────
            st.subheader("📊 Substation Status")
            cols = st.columns(len(active_subs))

            for i, sub_id in enumerate(active_subs):
                with cols[i]:
                    t = telemetry.get(sub_id, {})
                    h = health.get(sub_id, {})
                    status = h.get("risk_level", "Unknown")
                    score  = h.get("health_score", 0)
                    anomaly = h.get("anomaly_detected", False)

                    # Status colour
                    if status == "Healthy":
                        icon, colour = "🟢", "status-healthy"
                    elif status == "Warning":
                        icon, colour = "🟠", "status-warning"
                    else:
                        icon, colour = "🔴", "status-critical"

                    st.markdown(f"### {icon} Substation {sub_id}")
                    st.markdown(
                        f'<span class="{colour}">{status}</span>  '
                        f'{"⚠️ ANOMALY" if anomaly else ""}',
                        unsafe_allow_html=True,
                    )

                    # Health score progress bar
                    bar_colour = "normal" if score >= 80 else ("off" if score < 50 else "normal")
                    st.progress(int(score) / 100, text=f"Health: {score}/100")

                    # Metrics
                    c1, c2 = st.columns(2)
                    c1.metric("Voltage",     f"{t.get('voltage', 0):.1f} V")
                    c2.metric("Current",     f"{t.get('current', 0):.1f} A")
                    c1.metric("Temperature", f"{t.get('temperature', 0):.1f} °C")
                    c2.metric("Harmonics",   f"{t.get('harmonic_5th', 0):.1f} %")

                    actual_load = t.get("load_percentage", 0)
                    target_load = load_dist.get(sub_id, 33.3)
                    delta = round(target_load - actual_load, 1)
                    st.metric(
                        "Load",
                        f"{actual_load:.1f}%",
                        delta=f"Target: {target_load:.1f}%",
                        delta_color="off",
                    )

                    # Fault badges
                    fr = fault_reports.get(sub_id, {})
                    faults = fr.get("faults_detected", [])
                    if faults:
                        badges = " ".join(
                            f'<span class="fault-badge">{f["name"]}</span>'
                            for f in faults
                        )
                        st.markdown(f"**Faults:** {badges}", unsafe_allow_html=True)

            st.markdown("---")

            # ── Load distribution chart ───────────────────────────────────────
            st.subheader("⚖️ Load Distribution")
            if load_dist:
                df_load = pd.DataFrame({
                    "Substation": list(load_dist.keys()),
                    "Load (%)":   list(load_dist.values()),
                })
                st.bar_chart(df_load.set_index("Substation"))

            st.markdown("---")

            # ── Trend charts ──────────────────────────────────────────────────
            st.subheader("📈 Live Trends")
            tab_temp, tab_volt, tab_load, tab_health = st.tabs(
                ["🌡️ Temperature", "⚡ Voltage", "📦 Load %", "💚 Health Score"]
            )

            def build_trend_df(metric: str) -> pd.DataFrame:
                frames = {}
                for sub_id in active_subs:
                    buf = st.session_state.history[sub_id]
                    if buf[metric]:
                        frames[sub_id] = buf[metric]
                if not frames:
                    return pd.DataFrame()
                min_len = min(len(v) for v in frames.values())
                return pd.DataFrame({k: v[-min_len:] for k, v in frames.items()})

            with tab_temp:
                df = build_trend_df("temperature")
                if not df.empty:
                    st.line_chart(df)
                    st.caption("Temperature (°C) — danger threshold: 85°C")

            with tab_volt:
                df = build_trend_df("voltage")
                if not df.empty:
                    st.line_chart(df)
                    st.caption("Voltage (V) — normal range: 220–240V")

            with tab_load:
                df = build_trend_df("load_percentage")
                if not df.empty:
                    st.line_chart(df)
                    st.caption("Load (%) — normal range: 20–60%")

            with tab_health:
                df = build_trend_df("health_score")
                if not df.empty:
                    st.line_chart(df)
                    st.caption("Health Score (0–100) — Critical < 50, Warning < 80")

            st.markdown("---")

            # ── Alert feed ────────────────────────────────────────────────────
            st.subheader("🚨 Live Alert Feed")
            if alerts:
                for alert in alerts:
                    level = alert.get("level", "INFO")
                    msg   = f"[{alert['timestamp']}] **{alert['substation_id']}**: {alert['message']}"
                    if level == "CRITICAL":
                        st.error(msg)
                    elif level == "WARNING":
                        st.warning(msg)
                    else:
                        st.info(msg)
            else:
                st.success("No active alerts — all systems nominal.")

            # ── Footer ────────────────────────────────────────────────────────
            st.caption(
                f"Last updated: {datetime.now().strftime('%H:%M:%S')}  •  "
                f"Connected substations: {len(active_subs)}"
            )

    except requests.exceptions.ConnectionError:
        with placeholder.container():
            st.error(
                f"Cannot connect to API backend at {API_URL}.\n\n"
                "Make sure the backend is running:\n```\npython api/main.py\n```"
            )
    except Exception as e:
        with placeholder.container():
            st.error(f"Dashboard error: {e}")

    time.sleep(1.5)
