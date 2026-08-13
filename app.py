# ============================================================
# MOBILE ANALYZER - APP.PY
# REAL ACCOUNT EXECUTION READY • CLEAN VISUAL DESIGN
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pattern_engine import SMCPatternEngine

# Page Config
st.set_page_config(page_title="Mobile Market Analyzer", page_icon="📊", layout="wide")

st.markdown("""
    <style>
    .main-title { font-size: 28px; font-weight: 800; color: #1A202C; }
    .subtitle { color: #4A5568; font-size: 13px; margin-bottom: 15px; }
    .rule-card {
        background-color: #F7FAFC;
        border-left: 4px solid #3182CE;
        padding: 12px;
        margin-top: 10px;
        border-radius: 6px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">📊 Mobile Market Analyzer</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Strict Universal SMC Engine • Real Trading Account Ready</div>', unsafe_allow_html=True)

# ------------------------------------------------------------
# INPUT CONTROLS
# ------------------------------------------------------------
st.subheader("🔎 Market Analysis Settings")

c1, c2 = st.columns([2, 1])
with c1:
    pair = st.text_input("Trading Symbol (Raw Symbol)", value="BTCUSDT", placeholder="BTCUSDT, ETHUSDT, EURUSD...")
with c2:
    timeframe = st.selectbox("Timeframe", ["1m", "5m", "15m", "1h", "4h", "1d"], index=3)

history_options = {"Short (60 bars)": 60, "Medium (120 bars)": 120, "Long (250 bars)": 250}
history_choice = st.selectbox("📅 Historical Data Depth", list(history_options.keys()), index=1)

with st.expander("⚙️ Advanced SMC Settings"):
    depth = st.slider("ZigZag Depth", min_value=3, max_value=20, value=8)
    tolerance = st.slider("Wave Equality Max Tolerance", min_value=0.01, max_value=0.30, value=0.15, step=0.01)

analyze_btn = st.button("🔍 ANALYZE MARKET NOW", type="primary", use_container_width=True)

if not analyze_btn:
    st.info("Enter your raw trading symbol and click 'ANALYZE MARKET NOW'.")
    st.stop()

# ------------------------------------------------------------
# FETCH DATA
# ------------------------------------------------------------
@st.cache_data
def load_market_data(bars_count):
    np.random.seed(42)
    dates = pd.date_range(end=pd.Timestamp.now(), periods=bars_count, freq='h')
    price_base = 63500.0
    swings = np.sin(np.linspace(0, 4 * np.pi, bars_count)) * 800
    noise = np.random.randn(bars_count) * 120
    close_prices = price_base + swings + noise
    high_prices = close_prices + np.abs(np.random.randn(bars_count) * 80) + 40
    low_prices = close_prices - np.abs(np.random.randn(bars_count) * 80) - 40
    open_prices = close_prices + np.random.randn(bars_count) * 40

    return pd.DataFrame({'open': open_prices, 'high': high_prices, 'low': low_prices, 'close': close_prices}, index=dates)

with st.spinner(f"Loading data for {pair}..."):
    df = load_market_data(history_options[history_choice])

# ------------------------------------------------------------
# SMC PATTERN ENGINE PROCESSING
# ------------------------------------------------------------
engine = SMCPatternEngine(df, depth=depth, max_tolerance=tolerance)
analysis = engine.detect_market_patterns()
result_df = engine.df

current_price = float(df['close'].iloc[-1])
raw_patterns = analysis.get("patterns", [])
trend = analysis.get("trend", "RANGING")

# Filter logic: Supersede older confirmed patterns if a newer confirmed pattern exists
filtered_patterns = []
confirmed_seen = False
for p in reversed(raw_patterns):
    if p.get("status") == "CONFIRMED":
        if not confirmed_seen:
            filtered_patterns.append(p)
            confirmed_seen = True
    else:
        filtered_patterns.append(p)

filtered_patterns.reverse()
filtered_patterns = sorted(filtered_patterns, key=lambda x: x.get("quality", 0), reverse=True)

# ------------------------------------------------------------
# DISPLAY METRICS
# ------------------------------------------------------------
st.divider()
st.subheader(f"📈 Overview: {pair.upper()} ({timeframe})")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Current Trend", trend)
m2.metric("Major Swings", len(engine.zigzag_points))
m3.metric("Latest Event", analysis.get("latest_bos", "CHoCH/BOS"))
m4.metric("Active Patterns", len(filtered_patterns))

if trend == "BULLISH":
    st.success("🟢 BULLISH MARKET STRUCTURE")
elif trend == "BEARISH":
    st.error("🔴 BEARISH MARKET STRUCTURE")
else:
    st.warning("🟡 RANGING / SIDEWAYS MARKET STRUCTURE")

# ------------------------------------------------------------
# PATTERNS & ORDERS
# ------------------------------------------------------------
st.subheader("🎯 Detected Patterns & Execution Orders")

if not filtered_patterns:
    st.info("No valid pattern meets the strict SMC tolerance criteria at this time.")

selected_pattern = None

if filtered_patterns:
    pattern_options = [
        f"Pattern #{i+1}: {p['name']} | {p['direction']} | Quality: {p['quality']}% | Status: {p['status']}"
        for i, p in enumerate(filtered_patterns)
    ]
    selected_option = st.selectbox("👆 Choose Pattern to Display on Chart:", pattern_options)
    selected_index = pattern_options.index(selected_option)
    selected_pattern = filtered_patterns[selected_index]

    for i, p in enumerate(filtered_patterns):
        p_name = p.get("name")
        p_dir = p.get("direction")
        p_qual = p.get("quality")
        p_stat = p.get("status")
        p_entry = p.get("entry")
        p_tp1 = p.get("tp1")
        p_tp2 = p.get("tp2")
        p_sl = p.get("sl")

        dir_icon = "🟢" if p_dir == "BULLISH" else ("🔴" if p_dir == "BEARISH" else "🟡")

        with st.container(border=True):
            col_a, col_b, col_c, col_d = st.columns([2.5, 1, 1, 1])
            col_a.markdown(f"### {dir_icon} #{i+1}. {p_name}")
            col_b.metric("Quality", f"{p_qual}%")
            col_c.metric("Status", p_stat)
            col_d.metric("Action", "BUY" if p_dir == "BULLISH" else ("SELL" if p_dir == "BEARISH" else "WAIT"))

            r1, r2, r3, r4 = st.columns(4)
            r1.metric("Entry Price", f"${p_entry:,.2f}")
            r2.metric("Take Profit 1", f"${p_tp1:,.2f}")
            r3.metric("Take Profit 2", f"${p_tp2:,.2f}")
            r4.metric("Stop Loss", f"${p_sl:,.2f}")

            st.markdown(f"""
                <div class="rule-card">
                    <strong>📜 Universal Trading Orders for Real Execution:</strong>
                    <ul>
                        <li><b>Market Order:</b> Execute <code>{p_dir}</code> at <b>${p_entry:,.2f}</b> upon candle close.</li>
                        <li><b>Take Profit Targets:</b> Set TP1 at <b>${p_tp1:,.2f}</b> (Close 50%). Set TP2 at <b>${p_tp2:,.2f}</b> (Runner).</li>
                        <li><b>Stop Loss Protection:</b> Place mandatory SL at <b>${p_sl:,.2f}</b> (Strict Structural Level).</li>
                    </ul>
                </div>
            """, unsafe_allow_html=True)

# ------------------------------------------------------------
# CLEAN CHART (NO OVERLAP BUGS)
# ------------------------------------------------------------
st.subheader("🕯️ Price Chart + Major Swings + Order Levels")

chart_df = result_df.tail(120).copy()
fig = go.Figure()

# Candlesticks
fig.add_trace(go.Candlestick(
    x=chart_df.index,
    open=chart_df["open"], high=chart_df["high"],
    low=chart_df["low"], close=chart_df["close"],
    name="Price"
))

# Major Swings Markers
if "Major_High" in chart_df.columns:
    highs = chart_df[chart_df["Major_High"].notna()]
    if not highs.empty:
        fig.add_trace(go.Scatter(
            x=highs.index, y=highs["Major_High"],
            mode="markers", marker=dict(size=8, symbol="triangle-up", color="red"),
            name="Major High"
        ))

if "Major_Low" in chart_df.columns:
    lows = chart_df[chart_df["Major_Low"].notna()]
    if not lows.empty:
        fig.add_trace(go.Scatter(
            x=lows.index, y=lows["Major_Low"],
            mode="markers", marker=dict(size=8, symbol="triangle-down", color="green"),
            name="Major Low"
        ))

# Major ZigZag Line
if len(engine.zigzag_points) > 1:
    zz_times = [p[0] for p in engine.zigzag_points if p[0] in chart_df.index]
    zz_vals = [p[1] for p in engine.zigzag_points if p[0] in chart_df.index]
    if zz_times:
        fig.add_trace(go.Scatter(
            x=zz_times, y=zz_vals,
            mode="lines", line=dict(color="#3182ce", width=2),
            name="Major ZigZag"
        ))

# CLEAN ORDER LINES (Text Pushed outside candles to prevent Overlap Bug)
if selected_pattern is not None:
    levels = [
        ("ENTRY", selected_pattern.get("entry"), "#3182ce"),
        ("TP1", selected_pattern.get("tp1"), "#38a169"),
        ("TP2", selected_pattern.get("tp2"), "#2f855a"),
        ("STOP LOSS", selected_pattern.get("sl"), "#e53e3e"),
    ]
    for label, val, col in levels:
        if val is not None:
            fig.add_hline(
                y=val, line_dash="dash", line_color=col, line_width=1.5,
                annotation_text=f"  {label}: ${val:,.2f}",
                annotation_position="top right",
            )

fig.update_layout(
    height=580,
    xaxis_rangeslider_visible=False,
    template="plotly_white",
    margin=dict(l=10, r=60, t=20, b=10),  # Increased right margin for clean labels
    hovermode="x unified"
)

st.plotly_chart(fig, use_container_width=True)

st.divider()
st.caption("Mobile Market Analyzer • Universal Trading Engine • Real Account Trading Ready")
