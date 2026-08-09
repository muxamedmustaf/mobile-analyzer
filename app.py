import streamlit as st
import pandas as pd
import plotly.graph_objects as go

try:
    from data.market_data import fetch_market_data, get_timeframes
except ImportError:
    from market_data import fetch_market_data, get_timeframes

from structure.swings import detect_major_swings, analyze_market_structure
from pattern_engine import detect_patterns
from indicators.atr import calculate_atr
from indicators.ema import calculate_ema
from indicators.rsi import calculate_rsi

st.set_page_config(page_title="Mobile Market Analyzer", page_icon="📊", layout="wide")

st.markdown("""
<style>
.main-title {font-size:32px;font-weight:800;margin-bottom:5px;}
.subtitle {color:#888;margin-bottom:20px;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">📊 Mobile Market Analyzer</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Yahoo Finance • Major Swings • Chart Patterns • EMA • RSI • ATR • BOS / CHOCH</div>',
    unsafe_allow_html=True,
)

st.subheader("🔎 Market Analysis")
col1, col2 = st.columns([2, 1])

with col1:
    pair = st.text_input(
        "Pair / Symbol",
        value="BTC/USDT",
        placeholder="BTC/USDT, ETH/USDT, EUR/USD, XAU/USD...",
    )

with col2:
    timeframe = st.selectbox("Timeframe", get_timeframes(), index=6)

history_options = {
    "Short": "60d",
    "Medium": "180d",
    "Long": "1y",
    "Very Long": "5y",
    "Maximum": "max",
}

history = st.selectbox("📅 Historical Data", list(history_options.keys()), index=1)

with st.expander("⚙️ Advanced Swing Settings"):
    threshold = st.slider(
        "Major Swing Threshold",
        min_value=0.005,
        max_value=0.050,
        value=0.012,
        step=0.001,
        format="%.3f",
        help="Higher value = fewer and stronger major swings.",
    )

analyze = st.button("🔍 ANALYZE MARKET", type="primary", use_container_width=True)

if not analyze:
    st.info("Geli pair-ka, dooro timeframe-ka, kadib riix **ANALYZE MARKET**.")
    st.stop()

with st.spinner(f"📡 Yahoo Finance ayaa keenaya xogta {pair}..."):
    try:
        df = fetch_market_data(pair, timeframe, history_options[history])
    except Exception as error:
        st.error(f"❌ Xogta lama helin.\n\n{error}")
        st.stop()

if df is None or df.empty:
    st.error("❌ Yahoo Finance wax xog ah kama soo celin.")
    st.stop()

df = df.copy()
df.columns = [str(column).lower() for column in df.columns]

required_columns = {"open", "high", "low", "close"}
missing_columns = required_columns.difference(df.columns)

if missing_columns:
    st.error("❌ Market data columns ayaa maqan: " + ", ".join(sorted(missing_columns)))
    st.stop()

if len(df) < 50:
    st.warning(
        f"⚠️ Waxaa la helay {len(df)} candles oo keliya. "
        "Major swing engine wuxuu u baahan yahay ugu yaraan 50 candles."
    )
    st.stop()

with st.spinner("📐 Waxaa la xisaabinayaa ATR, EMA iyo RSI..."):
    try:
        df["ATR"] = calculate_atr(df, 14)
        df["EMA7"] = calculate_ema(df, 7)
        df["EMA15"] = calculate_ema(df, 15)
        df["EMA50"] = calculate_ema(df, 50)
        df["EMA200"] = calculate_ema(df, 200)
        df["RSI"] = calculate_rsi(df, 14)
    except Exception as error:
        st.error(f"❌ Indicator calculation error: {error}")
        st.stop()

with st.spinner("🔄 Waxaa la baarayaa major swings..."):
    try:
        structure_result = analyze_market_structure(df, threshold=threshold)
    except Exception as error:
        st.error(f"❌ Swing analysis error: {error}")
        st.stop()

result_df = structure_result["data"]
swings = structure_result["swings"]
trend = structure_result["trend"]
latest_bos = structure_result["bos"]
latest_choch = structure_result["choch"]

# Structure engine may return a new DataFrame, so restore indicators if needed.
for col in ["ATR", "EMA7", "EMA15", "EMA50", "EMA200", "RSI"]:
    if col not in result_df.columns:
        result_df[col] = df[col]

with st.spinner("🔍 Waxaa la baarayaa chart patterns..."):
    try:
        patterns = detect_patterns(result_df)
    except Exception as error:
        st.error(f"❌ Pattern engine error: {error}")
        st.stop()

latest = result_df.iloc[-1]

def fmt(value):
    try:
        if value is None or pd.isna(value):
            return "—"
        return f"{float(value):.6g}"
    except Exception:
        return "—"

close_value = latest.get("close")
atr_value = latest.get("ATR")
ema7_value = latest.get("EMA7")
ema15_value = latest.get("EMA15")
ema50_value = latest.get("EMA50")
ema200_value = latest.get("EMA200")
rsi_value = latest.get("RSI")

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

st.subheader("📐 Technical Indicators")
i1, i2, i3, i4, i5, i6 = st.columns(6)
with i1: st.metric("EMA 7", fmt(ema7_value))
with i2: st.metric("EMA 15", fmt(ema15_value))
with i3: st.metric("EMA 50", fmt(ema50_value))
with i4: st.metric("EMA 200", fmt(ema200_value))
with i5: st.metric("RSI 14", fmt(rsi_value))
with i6: st.metric("ATR 14", fmt(atr_value))

try:
    ema200_ok = float(close_value) > float(ema200_value)
except Exception:
    ema200_ok = False

try:
    rsi_ok = 30 < float(rsi_value) < 70
except Exception:
    rsi_ok = False

s1, s2, s3 = st.columns(3)
with s1:
    st.success("🟢 Price > EMA200") if ema200_ok else st.error("🔴 Price ≤ EMA200")
with s2:
    st.success("🟢 RSI 30–70") if rsi_ok else st.warning("🟡 RSI outside 30–70")
with s3:
    st.info(f"📏 ATR(14): {fmt(atr_value)}") if not pd.isna(atr_value) else st.warning("ATR lama helin")

if trend == "BULLISH":
    st.success("🟢 BULLISH MARKET STRUCTURE")
elif trend == "BEARISH":
    st.error("🔴 BEARISH MARKET STRUCTURE")
elif trend == "RANGING":
    st.warning("🟡 RANGING MARKET STRUCTURE")
else:
    st.info("⚪ MARKET STRUCTURE UNKNOWN")

st.subheader("🎯 Detected Chart Patterns")

if not patterns:
    st.info("Pattern la aqoonsaday lagama helin major swings-ka hadda jira.")
else:
    for pattern in patterns:
        name = pattern["name"]
        direction = pattern["direction"]
        quality = pattern["quality"]
        status = pattern["status"]
        reason = pattern["reason"]

        icon = "🟢" if direction == "BULLISH" else "🔴" if direction == "BEARISH" else "🟡"

        with st.container(border=True):
            p1, p2, p3 = st.columns([2, 1, 1])
            with p1: st.markdown(f"### {icon} {name}")
            with p2: st.metric("Quality", f"{quality}%")
            with p3: st.metric("Status", status)

            st.write(f"**Direction:** {direction}")
            st.write(f"**Reason:** {reason}")

            e1, e2, e3, e4 = st.columns(4)
            with e1: st.metric("Entry", fmt(pattern.get("entry")))
            with e2: st.metric("TP1", fmt(pattern.get("tp1")))
            with e3: st.metric("TP2", fmt(pattern.get("tp2")))
            with e4: st.metric("SL", fmt(pattern.get("sl")))

            if status == "CONFIRMED":
                st.success("✅ Pattern confirmed — trade decision still requires strategy conditions.")
            else:
                st.warning("⏳ Pattern forming — WAIT for confirmation.")

st.subheader("🕯️ Price Chart + Major Swings")
chart_df = result_df.tail(100).copy()
fig = go.Figure()

fig.add_trace(go.Candlestick(
    x=chart_df.index,
    open=chart_df["open"],
    high=chart_df["high"],
    low=chart_df["low"],
    close=chart_df["close"],
    name="Price",
))

for col in ["EMA7", "EMA15", "EMA50", "EMA200"]:
    if col in chart_df.columns:
        fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df[col], mode="lines", name=col))

if "zigzag" in chart_df.columns:
    zigzag = chart_df[chart_df["zigzag"].notna()]
    if not zigzag.empty:
        text = zigzag["structure"] if "structure" in zigzag.columns else None
        fig.add_trace(go.Scatter(
            x=zigzag.index, y=zigzag["zigzag"],
            mode="lines+markers+text", text=text,
            textposition="top center", name="Major ZigZag",
        ))

if "swing_high" in chart_df.columns:
    swing_highs = chart_df[chart_df["swing_high"].notna()]
    if not swing_highs.empty:
        fig.add_trace(go.Scatter(
            x=swing_highs.index, y=swing_highs["high"],
            mode="markers", name="Major High",
        ))

if "swing_low" in chart_df.columns:
    swing_lows = chart_df[chart_df["swing_low"].notna()]
    if not swing_lows.empty:
        fig.add_trace(go.Scatter(
            x=swing_lows.index, y=swing_lows["low"],
            mode="markers", name="Major Low",
        ))

fig.update_layout(
    height=700,
    xaxis_rangeslider_visible=False,
    hovermode="x unified",
    margin=dict(l=10, r=10, t=30, b=10),
)
st.plotly_chart(fig, use_container_width=True)

with st.expander("🔄 Major Swings"):
    if swings:
        st.dataframe(pd.DataFrame(swings), use_container_width=True, hide_index=True)
    else:
        st.info("Major swings lama helin.")

with st.expander("⚡ BOS / CHOCH Events"):
    if "BOS" in result_df.columns:
        bos_mask = result_df["BOS"].notna()
    else:
        bos_mask = pd.Series(False, index=result_df.index)

    if "CHOCH" in result_df.columns:
        choch_mask = result_df["CHOCH"].notna()
    else:
        choch_mask = pd.Series(False, index=result_df.index)

    events = result_df[bos_mask | choch_mask].copy()

    if events.empty:
        st.info("BOS ama CHOCH lama helin.")
    else:
        columns = [c for c in ["close", "zigzag_type", "structure", "BOS", "CHOCH"] if c in events.columns]
        st.dataframe(events[columns], use_container_width=True)

with st.expander("📐 Indicator Data"):
    columns = [c for c in ["close", "ATR", "EMA7", "EMA15", "EMA50", "EMA200", "RSI"] if c in result_df.columns]
    st.dataframe(result_df[columns].tail(30), use_container_width=True)

with st.expander("📋 Data Information"):
    st.write("**Source:** Yahoo Finance")
    st.write(f"**Yahoo Symbol:** {df.attrs.get('yahoo_symbol', '—')}")
    st.write(f"**Pair:** {pair.upper()}")
    st.write(f"**Timeframe:** {timeframe}")
    st.write(f"**Candles:** {len(df)}")
    st.write(f"**Latest Close:** {fmt(close_value)}")

with st.expander("🧾 Latest OHLC Data"):
    st.dataframe(result_df.tail(30), use_container_width=True)

st.divider()
st.caption("Mobile Analyzer • Yahoo Finance only • Major Swing Pattern Engine • EMA • RSI • ATR")
