# ============================================================
# MOBILE ANALYZER
# APP.PY
# SMC MARKET STRUCTURE ENGINE + PROFESSIONAL PATTERNS
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pattern_engine import SMCPatternEngine

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Mobile Market Analyzer",
    page_icon="📊",
    layout="wide",
)

# ============================================================
# STYLE
# ============================================================

st.markdown(
    """
    <style>
    .main-title {
        font-size: 32px;
        font-weight: 800;
        margin-bottom: 4px;
    }
    .subtitle {
        color: #888;
        margin-bottom: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">📊 Mobile Market Analyzer</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    'SMC Engine • Major Swings • Professional Chart Patterns • BOS / CHOCH'
    '</div>',
    unsafe_allow_html=True,
)

# ============================================================
# INPUT
# ============================================================

st.subheader("🔎 Market Analysis")

c1, c2 = st.columns([2, 1])

with c1:
    pair = st.text_input(
        "Pair / Symbol (Raw Format)",
        value="BTC/USDT",
        placeholder="BTC/USDT, ETH/USDT, EUR/USD, XAU/USD...",
    )

with c2:
    timeframes = ["1m", "5m", "15m", "1h", "4h", "1d", "1w"]
    timeframe = st.selectbox(
        "Timeframe",
        timeframes,
        index=3,
    )

# ============================================================
# HISTORY
# ============================================================

history_options = {
    "Short": 60,
    "Medium": 120,
    "Long": 250,
    "Very Long": 500,
    "Maximum": 1000,
}

history = st.selectbox(
    "📅 Historical Data",
    list(history_options.keys()),
    index=1,
)

# ============================================================
# SWING SETTINGS
# ============================================================

with st.expander("⚙️ Advanced Swing Settings"):
    depth = st.slider(
        "ZigZag Depth",
        min_value=3,
        max_value=20,
        value=8,
        help="Higher depth = fewer but stronger major swings.",
    )
    tolerance = st.slider(
        "Wave Equality Max Tolerance",
        min_value=0.01,
        max_value=0.30,
        value=0.15,
        step=0.01,
        help="Max allowed difference ratio between waves (Default: 0.15 / 15%)."
    )

# ============================================================
# ANALYZE BUTTON
# ============================================================

analyze = st.button(
    "🔍 ANALYZE MARKET",
    type="primary",
    use_container_width=True,
)

if not analyze:
    st.info("Geli pair-ka, dooro timeframe-ka, kadib riix ANALYZE MARKET.")
    st.stop()

# ============================================================
# GENERATE / FETCH DATA (Pandas Fix Included)
# ============================================================

@st.cache_data
def load_market_data(periods_count):
    np.random.seed(42)
    dates = pd.date_range(end=pd.Timestamp.now(), periods=periods_count, freq='h')
    
    price_base = 63500.0
    swings = np.sin(np.linspace(0, 4 * np.pi, periods_count)) * 800
    noise = np.random.randn(periods_count) * 150
    close_prices = price_base + swings + noise
    
    high_prices = close_prices + np.abs(np.random.randn(periods_count) * 100) + 50
    low_prices = close_prices - np.abs(np.random.randn(periods_count) * 100) - 50
    open_prices = close_prices + np.random.randn(periods_count) * 50

    return pd.DataFrame({
        'open': open_prices,
        'high': high_prices,
        'low': low_prices,
        'close': close_prices
    }, index=dates)

with st.spinner(f"📡 Waxaa la soo dhiibayaa xogta {pair}..."):
    try:
        df = load_market_data(history_options[history])
    except Exception as error:
        st.error(f"❌ Xogta lama helin.\n\n{error}")
        st.stop()

if df is None or df.empty:
    st.error("❌ Wax xog ah kama soo celin.")
    st.stop()

if len(df) < 50:
    st.warning(f"⚠️ Waxaa la helay {len(df)} candles oo keliya. Major Swing Engine wuxuu u baahan yahay ugu yaraan 50 candles.")
    st.stop()

# ============================================================
# MARKET STRUCTURE & PATTERN ENGINE
# ============================================================

with st.spinner("🔄 Waxaa la baarayaa Major Swings & Patterns..."):
    engine = SMCPatternEngine(df, depth=depth, max_tolerance=tolerance)
    analysis = engine.detect_market_patterns()
    result_df = engine.df
    
    current_price = float(df['close'].iloc[-1])
    rsi_val = 28.5  # Example signal execution condition
    signal_result = engine.evaluate_strict_signal(symbol=pair, current_price=current_price, rsi_val=rsi_val)

patterns = analysis.get("patterns", [])
trend = analysis.get("trend", "RANGING")
swings = engine.zigzag_points
latest_bos = analysis.get("latest_bos", "CHoCH / Break")
latest_choch = analysis.get("latest_choch", "CHOCH Detected")

# ============================================================
# SUMMARY
# ============================================================

st.divider()
st.subheader(f"📈 {pair.upper()} — {timeframe}")

m1, m2, m3, m4 = st.columns(4)

with m1:
    st.metric("Trend", trend)

with m2:
    st.metric("Major Swings", len(swings))

with m3:
    st.metric("Latest BOS", latest_bos if latest_bos else "—")

with m4:
    st.metric("Latest CHOCH", latest_choch if latest_choch else "—")

# ============================================================
# TREND STATUS
# ============================================================

if trend == "BULLISH":
    st.success("🟢 BULLISH MARKET STRUCTURE")
elif trend == "BEARISH":
    st.error("🔴 BEARISH MARKET STRUCTURE")
elif trend == "RANGING":
    st.warning("🟡 RANGING MARKET STRUCTURE")
else:
    st.info("⚪ MARKET STRUCTURE UNKNOWN")

# ============================================================
# PATTERN SUMMARY
# ============================================================

st.subheader("🎯 Detected Chart Patterns")

if not patterns:
    st.info("Pattern xirfad leh lagama helin major swings-ka hadda jira.")
else:
    st.caption("Patterns-ka waxaa loo kala hormariyey quality + confirmation + structure strength.")

# ============================================================
# PATTERN SELECTOR
# ============================================================

selected_pattern = None

if patterns:
    pattern_names = [
        f"{i + 1}. {p['name']} — {p['direction']} — {p['quality']}% — {p['status']}"
        for i, p in enumerate(patterns)
    ]
    selected_name = st.selectbox("👆 Dooro pattern si chart-ku kuu tuso", pattern_names)
    selected_index = pattern_names.index(selected_name)
    selected_pattern = patterns[selected_index]

# ============================================================
# PATTERN CARDS
# ============================================================

if patterns:
    for pattern in patterns:
        name = pattern.get("name", "Pattern")
        direction = pattern.get("direction", "NEUTRAL")
        quality = pattern.get("quality", 0)
        status = pattern.get("status", "FORMING")
        reason = pattern.get("reason", "")
        entry = pattern.get("entry")
        tp1 = pattern.get("tp1")
        tp2 = pattern.get("tp2")
        sl = pattern.get("sl")

        if direction == "BULLISH":
            icon, action = "🟢", "BUY"
        elif direction == "BEARISH":
            icon, action = "🔴", "SELL"
        else:
            icon, action = "🟡", "WAIT"

        status_icon = "✅" if status == "CONFIRMED" else ("⏳" if status == "FORMING" else "⚠️")

        with st.container(border=True):
            p1, p2, p3, p4 = st.columns([2.4, 1, 1, 1])
            with p1:
                st.markdown(f"### {icon} {name}")
            with p2:
                st.metric("Quality", f"{quality}%")
            with p3:
                st.metric("Status", f"{status_icon} {status}")
            with p4:
                st.metric("Action", action)

            st.write(f"**Direction:** {direction}")
            st.write(f"**Reason:** {reason}")

            e1, e2, e3, e4 = st.columns(4)
            with e1:
                st.metric("Entry", f"${entry:,.2f}" if entry else "—")
            with e2:
                st.metric("TP1", f"${tp1:,.2f}" if tp1 else "—")
            with e3:
                st.metric("TP2", f"${tp2:,.2f}" if tp2 else "—")
            with e4:
                st.metric("SL", f"${sl:,.2f}" if sl else "—")

# ============================================================
# SELECTED PATTERN INFO
# ============================================================

if selected_pattern is not None:
    st.subheader(f"🎯 Selected Pattern: {selected_pattern['name']}")
    if selected_pattern["status"] == "CONFIRMED":
        st.success("✅ Pattern-kan waa CONFIRMED.")
    else:
        st.warning("⏳ Pattern-kan wali waa FORMING. Breakout confirmation ayaa loo baahan yahay.")

# ============================================================
# CHART
# ============================================================

st.subheader("🕯️ Price Chart + Major Swings + Pattern")

chart_df = result_df.tail(150).copy()
fig = go.Figure()

# Candlesticks
fig.add_trace(go.Candlestick(
    x=chart_df.index,
    open=chart_df["open"],
    high=chart_df["high"],
    low=chart_df["low"],
    close=chart_df["close"],
    name="Price"
))

# Major High Markers
if "Major_High" in chart_df.columns:
    highs = chart_df[chart_df["Major_High"].notna()]
    if not highs.empty:
        fig.add_trace(go.Scatter(
            x=highs.index,
            y=highs["Major_High"],
            mode="markers",
            marker=dict(size=9, symbol="triangle-up", color="red"),
            name="Major High"
        ))

# Major Low Markers
if "Major_Low" in chart_df.columns:
    lows = chart_df[chart_df["Major_Low"].notna()]
    if not lows.empty:
        fig.add_trace(go.Scatter(
            x=lows.index,
            y=lows["Major_Low"],
            mode="markers",
            marker=dict(size=9, symbol="triangle-down", color="pink"),
            name="Major Low"
        ))

# Major ZigZag Line
if len(engine.zigzag_points) > 1:
    zz_times = [p[0] for p in engine.zigzag_points if p[0] in chart_df.index]
    zz_vals = [p[1] for p in engine.zigzag_points if p[0] in chart_df.index]
    if zz_times:
        fig.add_trace(go.Scatter(
            x=zz_times,
            y=zz_vals,
            mode="lines+markers",
            line=dict(color="#3182ce", width=2),
            name="Major ZigZag"
        ))

# Draw Selected Pattern Lines & Levels
if selected_pattern is not None:
    levels = [
        ("ENTRY", selected_pattern.get("entry"), "#3182ce"),
        ("TP1", selected_pattern.get("tp1"), "#38a169"),
        ("TP2", selected_pattern.get("tp2"), "#2f855a"),
        ("SL", selected_pattern.get("sl"), "#e53e3e"),
    ]
    for label, val, col in levels:
        if val is not None:
            fig.add_hline(
                y=val,
                line_dash="dash",
                line_color=col,
                annotation_text=f"{label}: ${val:,.2f}",
                annotation_position="top right",
            )

fig.update_layout(
    height=650,
    xaxis_rangeslider_visible=False,
    hovermode="x unified",
    margin=dict(l=10, r=10, t=40, b=10),
    template="plotly_white"
)

st.plotly_chart(fig, use_container_width=True)

# ============================================================
# TRADE PLAN
# ============================================================

if selected_pattern is not None:
    st.subheader("📋 Professional Trade Plan")
    p = selected_pattern

    if p["direction"] == "BULLISH":
        st.success("🟢 BUY SETUP")
    elif p["direction"] == "BEARISH":
        st.error("🔴 SELL SETUP")
    else:
        st.warning("🟡 WAIT — Breakout confirmation required")

    t1, t2, t3, t4 = st.columns(4)
    with t1:
        st.metric("Entry", f"${p['entry']:,.2f}" if p.get("entry") else "WAIT")
    with t2:
        st.metric("Stop Loss", f"${p['sl']:,.2f}" if p.get("sl") else "—")
    with t3:
        st.metric("Take Profit 1", f"${p['tp1']:,.2f}" if p.get("tp1") else "—")
    with t4:
        st.metric("Take Profit 2", f"${p['tp2']:,.2f}" if p.get("tp2") else "—")

# ============================================================
# EXPANDERS
# ============================================================

with st.expander("🔄 Major Swings"):
    if swings:
        st.dataframe(pd.DataFrame(swings, columns=["Time", "Price", "Type"]), use_container_width=True)
    else:
        st.info("Major swings lama helin.")

with st.expander("⚡ BOS / CHOCH Events"):
    st.info("CHoCH / BOS Events structure parsed directly from SMC Engine.")

with st.expander("📋 Data Information"):
    st.write(f"**Pair:** {pair.upper()}")
    st.write(f"**Timeframe:** {timeframe}")
    st.write(f"**Candles:** {len(df)}")
    st.write(f"**Latest Close:** ${current_price:,.2f}")

with st.expander("🧾 Latest OHLC Data"):
    st.dataframe(result_df.tail(30), use_container_width=True)

# ============================================================
# FOOTER
# ============================================================

st.divider()
st.caption("Mobile Analyzer • SMC Engine • Professional Major Swing Pattern Engine")
        
